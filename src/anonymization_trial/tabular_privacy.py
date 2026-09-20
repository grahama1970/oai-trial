"""Deterministic privacy-model metrics for policy-declared tabular columns.

The module deliberately does not infer quasi-identifiers: callers must declare
columns, keeping transformation authority with the approved policy/operator.
"""

from __future__ import annotations

import csv
import fcntl
import hashlib
import itertools
import json
import math
import os
import secrets
import stat
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from collections.abc import Callable
from pathlib import Path


def audit_csv(
    path: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    raw_path: Path | None = None,
) -> dict:
    if not quasi_identifiers or len(set(quasi_identifiers)) != len(quasi_identifiers):
        raise ValueError("quasi_identifiers must be a non-empty unique list")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [name for name in [*quasi_identifiers, sensitive] if name not in fields]
        if missing:
            raise ValueError(f"missing declared columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("tabular audit requires at least one record")
    raw_records = len(rows)
    if raw_path is not None:
        raw_fields, raw_rows = _read_csv(raw_path)
        missing_raw = [name for name in [*quasi_identifiers, sensitive] if name not in raw_fields]
        if missing_raw:
            raise ValueError(f"raw input missing declared columns: {', '.join(missing_raw)}")
        if len(raw_rows) < len(rows):
            raise ValueError("raw input cannot contain fewer records than anonymized input")
        raw_records = len(raw_rows)

    classes: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        classes[tuple(row[name] for name in quasi_identifiers)].append(row)
    global_sensitive = Counter(row[sensitive] for row in rows)
    global_total = len(rows)

    class_counts = [Counter(row[sensitive] for row in group) for group in classes.values()]
    k = min(len(group) for group in classes.values())
    diversity = min(len(counts) for counts in class_counts)
    minimum_entropy_nats = min(
        -sum(
            (count / sum(counts.values())) * math.log(count / sum(counts.values()))
            for count in counts.values()
        )
        for counts in class_counts
    )
    entropy_diversity = math.exp(minimum_entropy_nats)
    alpha = max(max(counts.values()) / sum(counts.values()) for counts in class_counts)
    recursive_ratios: dict[str, float | None] = {}
    for l_value in range(2, max(len(counts) for counts in class_counts) + 1):
        ratios = []
        for counts in class_counts:
            ranked = sorted(counts.values(), reverse=True)
            if len(ranked) < l_value or not sum(ranked[l_value - 1 :]):
                ratios = []
                break
            ratios.append(ranked[0] / sum(ranked[l_value - 1 :]))
        recursive_ratios[str(l_value)] = round(max(ratios), 12) if ratios else None
    basic_beta = 0.0
    enhanced_beta = 0.0
    for counts in class_counts:
        local_total = sum(counts.values())
        for value, global_count in global_sensitive.items():
            global_probability = global_count / global_total
            local_probability = counts[value] / local_total
            increase = max(0.0, (local_probability - global_probability) / global_probability)
            basic_beta = max(basic_beta, increase)
            enhanced_beta = max(enhanced_beta, min(increase, -math.log(global_probability)))
    t = 0.0
    values = set(global_sensitive)
    for group in classes.values():
        local = Counter(row[sensitive] for row in group)
        distance = 0.5 * sum(
            abs(local[value] / len(group) - global_sensitive[value] / global_total)
            for value in values
        )
        t = max(t, distance)
    suppressed_records = raw_records - len(rows)
    class_sizes = [len(group) for group in classes.values()]
    classification_errors = suppressed_records + sum(
        len(group) - max(Counter(row[sensitive] for row in group).values())
        for group in classes.values()
    )
    global_entropy = -sum(
        (count / global_total) * math.log(count / global_total)
        for count in global_sensitive.values()
    )
    delta_disclosure = 0.0
    for counts in class_counts:
        local_total = sum(counts.values())
        for value, count in counts.items():
            ratio = (count / local_total) / (global_sensitive[value] / global_total)
            delta_disclosure = max(delta_disclosure, abs(math.log(ratio)))
    qi_statistics = {}
    for name in quasi_identifiers:
        counts = Counter(row[name] for row in rows)
        stats: dict[str, int | float | bool] = {
            "distinct_values": len(counts),
            "minimum_frequency": min(counts.values()),
            "maximum_frequency": max(counts.values()),
        }
        try:
            numeric = [float(row[name]) for row in rows]
        except ValueError:
            stats["numeric"] = False
        else:
            ordered = sorted(numeric)
            midpoint = len(ordered) // 2
            median = (
                ordered[midpoint]
                if len(ordered) % 2
                else (ordered[midpoint - 1] + ordered[midpoint]) / 2
            )
            mean = sum(numeric) / len(numeric)
            stats.update(
                numeric=True,
                mean=round(mean, 12),
                median=round(median, 12),
                variance=round(sum((value - mean) ** 2 for value in numeric) / len(numeric), 12),
            )
        qi_statistics[name] = stats
    ordered_sizes = sorted(class_sizes)
    middle = len(ordered_sizes) // 2
    median_size = (
        ordered_sizes[middle]
        if len(ordered_sizes) % 2
        else (ordered_sizes[middle - 1] + ordered_sizes[middle]) / 2
    )
    metrics = {
        "schema": "tabular_privacy_metrics.v2",
        "records": len(rows),
        "raw_records": raw_records,
        "suppressed_records": suppressed_records,
        "equivalence_classes": len(classes),
        "equivalence_class_statistics": {
            "count": len(class_sizes),
            "minimum_size": min(class_sizes),
            "maximum_size": max(class_sizes),
            "mean_size": round(sum(class_sizes) / len(class_sizes), 12),
            "median_size": round(median_size, 12),
        },
        "quasi_identifier_count": len(quasi_identifiers),
        "quasi_identifier_statistics": qi_statistics,
        "average_equivalence_class_size": round(len(rows) / (len(classes) * k), 12),
        "discernibility_metric": (
            sum(size**2 for size in class_sizes) + suppressed_records * raw_records
        ),
        "classification_metric": round(classification_errors / raw_records, 12),
        "average_reidentification_risk": round(
            sum(1 / size for size in class_sizes) / len(class_sizes), 12
        ),
        "maximum_reidentification_risk": round(1 / k, 12),
        "sensitive_attribute_entropy_nats": round(global_entropy, 12),
        "delta_disclosure": round(delta_disclosure, 12),
        "k_anonymity": k,
        "l_diversity": diversity,
        "entropy_logarithm": "natural",
        "minimum_entropy_nats": round(minimum_entropy_nats, 12),
        "entropy_effective_l": round(entropy_diversity, 12),
        "entropy_l_diversity": math.floor(entropy_diversity + 1e-12),
        "alpha_k_anonymity": {"k": k, "maximum_sensitive_frequency": round(alpha, 12)},
        "recursive_c_l_diversity": {"minimum_c_by_l": recursive_ratios},
        "basic_beta_likeness": round(basic_beta, 12),
        "enhanced_beta_likeness": round(enhanced_beta, 12),
        "categorical_total_variation_t_closeness": round(t, 12),
        "t_closeness": round(t, 12),
        "raw_values_persisted": False,
    }
    try:
        numeric_global = sorted(float(row[sensitive]) for row in rows)
    except ValueError:
        numeric_global = []
    if numeric_global:
        span = numeric_global[-1] - numeric_global[0]
        emd = 0.0
        if span:
            support = sorted(set(numeric_global))
            for group in classes.values():
                local = sorted(float(row[sensitive]) for row in group)
                distance = 0.0
                for left, right in zip(support, support[1:], strict=False):
                    global_cdf = sum(value <= left for value in numeric_global) / len(
                        numeric_global
                    )
                    local_cdf = sum(value <= left for value in local) / len(local)
                    distance += abs(global_cdf - local_cdf) * (right - left)
                emd = max(emd, distance / span)
        metrics["numeric_emd_t_closeness"] = round(emd, 12)
    return metrics


# The exact sampler below has privacy loss ln(2). Requiring a declared epsilon
# of at least 0.7 is conservative because ln(2) < 0.7.
_MIN_NOISE_EPSILON = Decimal("0.7")
_MAX_NOISE_EPSILON = Decimal("100")
_FORMAL_EPSILON_UPPER_BOUND = Decimal("0.7")


def _validated_epsilon(value: object, label: str = "epsilon") -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f"{label} must be numeric")
    try:
        epsilon = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError(f"{label} must be numeric") from error
    if not epsilon.is_finite() or not _MIN_NOISE_EPSILON <= epsilon <= _MAX_NOISE_EPSILON:
        raise ValueError(
            f"{label} must be finite and between {_MIN_NOISE_EPSILON} and {_MAX_NOISE_EPSILON}"
        )
    return epsilon


def _sample_two_sided_geometric(randbelow: Callable[[int], int]) -> int:
    """Sample P(0)=1/3 and P(±m)=1/(3*2**m) using exact fair bits."""
    while (branch := randbelow(4)) == 3:
        pass
    if branch == 0:
        return 0
    magnitude = 1
    while randbelow(2) == 0:
        magnitude += 1
    return magnitude if branch == 1 else -magnitude


def release_dp_count(
    path: Path,
    column: str,
    equals: str,
    epsilon: float | Decimal | str,
    *,
    random_below: Callable[[int], int] | None = None,
) -> dict:
    """Release a sensitivity-one count with exact two-sided geometric noise.

    The exact integer distribution has adjacent likelihood ratio at most 2,
    hence privacy loss ln(2), conservatively bounded by declared epsilon >= 0.7.
    The predicate is deliberately omitted because it may itself be sensitive.
    """
    epsilon_decimal = _validated_epsilon(epsilon)
    fields, rows = _read_csv(path, allow_empty=True)
    if column not in fields:
        raise ValueError("missing declared predicate column")
    noise = _sample_two_sided_geometric(random_below or secrets.randbelow)
    noisy_count = max(0, sum(row[column] == equals for row in rows) + noise)
    return {
        "schema": "differentially_private_count.v1",
        "mechanism": "exact_two_sided_geometric_p_half",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound": float(_FORMAL_EPSILON_UPPER_BOUND),
        "adjacency": "add_remove_one_record",
        "epsilon": float(epsilon_decimal),
        "sensitivity": 1,
        "noisy_count": noisy_count,
        "clamped_to_nonnegative": True,
        "composition": "single_query_only",
        "cryptographic_randomness": random_below is None,
        "raw_values_persisted": False,
    }


def release_dp_counts(
    path: Path,
    queries: list[dict[str, object]],
    maximum_epsilon: float | Decimal | str,
    *,
    random_below: Callable[[int], int] | None = None,
) -> dict:
    """Release multiple noisy counts with exact, fail-closed budget accounting."""
    maximum_decimal = _validated_epsilon(maximum_epsilon, "maximum_epsilon")
    maximum_fraction = Fraction(maximum_decimal)
    if not queries:
        raise ValueError("queries must be a non-empty list")
    normalized: list[tuple[str, str, Decimal]] = []
    epsilon_values: list[Decimal] = []
    for query in queries:
        if set(query) != {"column", "equals", "epsilon"}:
            raise ValueError("each query must contain only column, equals, and epsilon")
        column, equals, epsilon = query["column"], query["equals"], query["epsilon"]
        if not isinstance(column, str) or not column or not isinstance(equals, str):
            raise ValueError("query column and equals must be strings")
        epsilon_decimal = _validated_epsilon(epsilon, "query epsilon")
        normalized.append((column, equals, epsilon_decimal))
        epsilon_values.append(epsilon_decimal)
    total_fraction = sum((Fraction(value) for value in epsilon_values), Fraction(0))
    if total_fraction > maximum_fraction:
        raise ValueError("composed epsilon exceeds maximum_epsilon")
    releases = [
        release_dp_count(path, column, equals, epsilon, random_below=random_below)
        for column, equals, epsilon in normalized
    ]
    return {
        "schema": "differentially_private_count_batch.v1",
        "mechanism": "exact_two_sided_geometric_p_half",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound_per_query": float(_FORMAL_EPSILON_UPPER_BOUND),
        "adjacency": "add_remove_one_record",
        "composition": "basic_sequential_composition",
        "query_count": len(releases),
        "total_epsilon": float(total_fraction),
        "maximum_epsilon": float(maximum_fraction),
        "remaining_epsilon": float(maximum_fraction - total_fraction),
        "noisy_counts": [release["noisy_count"] for release in releases],
        "cryptographic_randomness": random_below is None,
        "raw_values_persisted": False,
    }


def _spend_persistent_epsilon(
    ledger_path: Path,
    budget_id: str,
    maximum_epsilon: float | Decimal | str,
    requested_epsilon: float | Decimal | str | Fraction,
    producer: Callable[[], dict],
) -> tuple[dict, str, Fraction, Fraction]:
    """Atomically spend epsilon before any producer can publish release bytes."""
    if not budget_id:
        raise ValueError("budget_id must be non-empty")
    maximum = Fraction(_validated_epsilon(maximum_epsilon, "maximum_epsilon"))
    requested = (
        requested_epsilon
        if isinstance(requested_epsilon, Fraction)
        else Fraction(_validated_epsilon(requested_epsilon, "requested_epsilon"))
    )
    if requested <= 0:
        raise ValueError("requested_epsilon must be positive")
    budget_hash = hashlib.sha256(budget_id.encode("utf-8")).hexdigest()
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(ledger_path, flags, 0o600)
    with os.fdopen(descriptor, "r+", encoding="utf-8") as ledger:
        if not stat.S_ISREG(os.fstat(ledger.fileno()).st_mode):
            raise ValueError("budget ledger must be a regular file")
        fcntl.flock(ledger, fcntl.LOCK_EX)
        content = ledger.read()
        state = json.loads(content) if content else None
        if state is None:
            spent = Fraction(0)
        else:
            if (
                state.get("schema") != "dp_budget_ledger.v1"
                or state.get("budget_id_sha256") != budget_hash
                or Fraction(state["maximum_numerator"], state["maximum_denominator"]) != maximum
            ):
                raise ValueError("budget ledger identity or maximum_epsilon mismatch")
            spent = Fraction(state["spent_numerator"], state["spent_denominator"])
        if spent + requested > maximum:
            raise ValueError("persistent composed epsilon exceeds maximum_epsilon")
        cumulative = spent + requested
        persisted = {
            "schema": "dp_budget_ledger.v1",
            "budget_id_sha256": budget_hash,
            "maximum_numerator": maximum.numerator,
            "maximum_denominator": maximum.denominator,
            "spent_numerator": cumulative.numerator,
            "spent_denominator": cumulative.denominator,
        }
        ledger.seek(0)
        json.dump(persisted, ledger, sort_keys=True, separators=(",", ":"))
        ledger.truncate()
        ledger.flush()
        os.fsync(ledger.fileno())
        result = producer()
    return result, budget_hash, cumulative, maximum


def release_dp_counts_persistent(
    path: Path,
    queries: list[dict[str, object]],
    maximum_epsilon: float | Decimal | str,
    ledger_path: Path,
    budget_id: str,
    *,
    random_below: Callable[[int], int] | None = None,
) -> dict:
    """Atomically reserve and spend a privacy budget across CLI invocations."""
    requested = sum(
        (
            Fraction(_validated_epsilon(query.get("epsilon"), "query epsilon"))
            for query in queries
            if isinstance(query, dict)
        ),
        Fraction(0),
    )
    if len(queries) == 0 or requested <= 0:
        raise ValueError("queries must be a non-empty list")
    result, budget_hash, cumulative, maximum = _spend_persistent_epsilon(
        ledger_path,
        budget_id,
        maximum_epsilon,
        requested,
        lambda: release_dp_counts(path, queries, maximum_epsilon, random_below=random_below),
    )
    result.update(
        {
            "schema": "differentially_private_count_persistent_batch.v1",
            "budget_id_sha256": budget_hash,
            "cumulative_epsilon": float(cumulative),
            "persistent_remaining_epsilon": float(maximum - cumulative),
            "budget_ledger_contains_predicates": False,
        }
    )
    return result


def release_dp_synthetic_histogram(
    path: Path,
    output: Path,
    dimensions: list[str],
    domains: dict[str, list[str]],
    epsilon: float | Decimal | str,
    *,
    random_below: Callable[[int], int] | None = None,
) -> dict:
    """Release a noisy multidimensional categorical histogram as synthetic rows.

    Domains are explicit operator-approved public categories. The receipt keeps
    only aggregate dimensions and sizes; the synthetic CSV is the release.
    """
    if output.exists():
        raise FileExistsError("output already exists")
    if not dimensions or len(set(dimensions)) != len(dimensions):
        raise ValueError("dimensions must be a non-empty unique list")
    epsilon_decimal = _validated_epsilon(epsilon)
    fields, rows = _read_csv(path, allow_empty=True)
    missing = [name for name in dimensions if name not in fields]
    if missing:
        raise ValueError(f"missing declared dimensions: {', '.join(missing)}")
    normalized_domains: dict[str, list[str]] = {}
    for dimension in dimensions:
        values = domains.get(dimension)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or value == "" for value in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"domain must declare unique string values for {dimension}")
        normalized_domains[dimension] = values
    allowed = {name: set(values) for name, values in normalized_domains.items()}
    for row in rows:
        for dimension in dimensions:
            if row[dimension] not in allowed[dimension]:
                raise ValueError("input contains a value outside the declared public domain")

    counts = Counter(tuple(row[dimension] for dimension in dimensions) for row in rows)
    cells = list(itertools.product(*(normalized_domains[name] for name in dimensions)))
    synthetic_rows: list[dict[str, str]] = []
    for cell in cells:
        noisy = max(
            0,
            counts[cell]
            + _sample_two_sided_geometric(random_below or secrets.randbelow),
        )
        synthetic_rows.extend(
            dict(zip(dimensions, cell, strict=True)) for _ in range(noisy)
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=dimensions, lineterminator="\n")
            writer.writeheader()
            writer.writerows(synthetic_rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        Path(temporary).unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        raise
    return {
        "schema": "differentially_private_synthetic_histogram.v1",
        "mechanism": "exact_two_sided_geometric_p_half_multidimensional_histogram",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound": float(_FORMAL_EPSILON_UPPER_BOUND),
        "adjacency": "add_remove_one_record",
        "epsilon": float(epsilon_decimal),
        "sensitivity": 1,
        "composition": "histogram_parallel_cells_one_record_one_cell",
        "dimension_count": len(dimensions),
        "domain_cell_count": len(cells),
        "domain_sizes": [len(normalized_domains[name]) for name in dimensions],
        "source_records": len(rows),
        "synthetic_records": len(synthetic_rows),
        "cryptographic_randomness": random_below is None,
        "receipt_contains_domain_values": False,
        "raw_values_persisted": False,
    }


def release_dp_synthetic_histogram_persistent(
    path: Path,
    output: Path,
    dimensions: list[str],
    domains: dict[str, list[str]],
    epsilon: float | Decimal | str,
    maximum_epsilon: float | Decimal | str,
    ledger_path: Path,
    budget_id: str,
    *,
    random_below: Callable[[int], int] | None = None,
) -> dict:
    """Release a synthetic histogram while composing epsilon across invocations."""
    result, budget_hash, cumulative, maximum = _spend_persistent_epsilon(
        ledger_path,
        budget_id,
        maximum_epsilon,
        epsilon,
        lambda: release_dp_synthetic_histogram(
            path, output, dimensions, domains, epsilon, random_below=random_below
        ),
    )
    result.update(
        {
            "schema": "differentially_private_synthetic_histogram_persistent.v1",
            "composition": "basic_sequential_composition_persistent_ledger",
            "budget_id_sha256": budget_hash,
            "cumulative_epsilon": float(cumulative),
            "persistent_remaining_epsilon": float(maximum - cumulative),
            "budget_ledger_contains_domain_values": False,
            "budget_ledger_contains_raw_values": False,
        }
    )
    return result


def audit_delta_presence(
    release_path: Path, population_path: Path, quasi_identifiers: list[str]
) -> dict:
    """Compute ARX-style sample presence bounds for declared QI classes.

    Both inputs remain local and only aggregate extrema are returned. A release
    class absent from (or more frequent than) the reference population fails
    closed instead of yielding a misleading probability.
    """
    if not quasi_identifiers or len(set(quasi_identifiers)) != len(quasi_identifiers):
        raise ValueError("quasi_identifiers must be a non-empty unique list")
    release_fields, release_rows = _read_csv(release_path)
    population_fields, population_rows = _read_csv(population_path)
    if not release_rows or not population_rows:
        raise ValueError("delta-presence audit requires non-empty release and population")
    for label, fields in (("release", release_fields), ("population", population_fields)):
        missing = [name for name in quasi_identifiers if name not in fields]
        if missing:
            raise ValueError(f"{label} missing declared columns: {', '.join(missing)}")
    release_counts = Counter(
        tuple(row[name] for name in quasi_identifiers) for row in release_rows
    )
    population_counts = Counter(
        tuple(row[name] for name in quasi_identifiers) for row in population_rows
    )
    invalid = [
        group
        for group, count in release_counts.items()
        if count > population_counts.get(group, 0)
    ]
    if invalid:
        raise ValueError("release is not a QI-class subset of the reference population")
    probabilities = [
        count / population_counts[group] for group, count in release_counts.items()
    ]
    return {
        "schema": "delta_presence_metrics.v1",
        "release_records": len(release_rows),
        "population_records": len(population_rows),
        "quasi_identifier_count": len(quasi_identifiers),
        "equivalence_classes": len(release_counts),
        "minimum_delta_presence": round(min(probabilities), 12),
        "maximum_delta_presence": round(max(probabilities), 12),
        "raw_values_persisted": False,
    }


def audit_population_reidentification(
    release_path: Path, population_path: Path, quasi_identifiers: list[str]
) -> dict:
    """Compute conservative prosecutor/journalist/marketer risk aggregates.

    The population must contain every released QI class with at least the released
    multiplicity. Only counts and extrema leave this function; QI tuples do not.
    """
    if not quasi_identifiers or len(set(quasi_identifiers)) != len(quasi_identifiers):
        raise ValueError("quasi_identifiers must be a non-empty unique list")
    release_fields, release_rows = _read_csv(release_path)
    population_fields, population_rows = _read_csv(population_path)
    if not release_rows or not population_rows:
        raise ValueError("population risk audit requires non-empty release and population")
    for label, fields in (("release", release_fields), ("population", population_fields)):
        missing = [name for name in quasi_identifiers if name not in fields]
        if missing:
            raise ValueError(f"{label} missing declared columns: {', '.join(missing)}")
    release_counts = Counter(
        tuple(row[name] for name in quasi_identifiers) for row in release_rows
    )
    population_counts = Counter(
        tuple(row[name] for name in quasi_identifiers) for row in population_rows
    )
    if any(count > population_counts.get(group, 0) for group, count in release_counts.items()):
        raise ValueError("release is not a QI-class subset of the reference population")

    sample_unique_records = sum(
        count for group, count in release_counts.items() if count == 1
    )
    population_unique_records = sum(
        count for group, count in release_counts.items() if population_counts[group] == 1
    )
    return {
        "schema": "population_reidentification_risk.v1",
        "release_records": len(release_rows),
        "population_records": len(population_rows),
        "quasi_identifier_count": len(quasi_identifiers),
        "equivalence_classes": len(release_counts),
        "sample_unique_records": sample_unique_records,
        "population_unique_records": population_unique_records,
        "sample_uniqueness_rate": round(sample_unique_records / len(release_rows), 12),
        "population_uniqueness_rate": round(population_unique_records / len(release_rows), 12),
        "maximum_prosecutor_risk": round(max(1 / count for count in release_counts.values()), 12),
        "maximum_journalist_risk": round(
            max(1 / population_counts[group] for group in release_counts), 12
        ),
        "marketer_success_rate": round(
            sum(count / population_counts[group] for group, count in release_counts.items())
            / len(release_rows),
            12,
        ),
        "raw_values_persisted": False,
    }


def audit_multiple_sensitive_attributes(
    path: Path,
    quasi_identifiers: list[str],
    sensitive_attributes: list[str],
    raw_path: Path | None = None,
    *,
    condition_on_other_sensitive: bool = False,
) -> dict:
    """Audit each sensitive attribute, optionally conditioning on the others.

    ``condition_on_other_sensitive`` matches pyCANON's ``gen=False`` convention:
    while auditing one sensitive attribute, every other sensitive attribute is
    included in the equivalence-class key. Receipts retain metrics, never tuples.
    """
    attributes = [name.strip() for name in sensitive_attributes if name.strip()]
    if not attributes or len(set(attributes)) != len(attributes):
        raise ValueError("sensitive_attributes must be a non-empty unique list")
    if set(attributes) & set(quasi_identifiers):
        raise ValueError("sensitive attributes must not also be quasi-identifiers")
    audits = {
        name: audit_csv(
            path,
            [
                *quasi_identifiers,
                *(
                    other
                    for other in attributes
                    if condition_on_other_sensitive and other != name
                ),
            ],
            name,
            raw_path,
        )
        for name in attributes
    }
    return {
        "schema": "multiple_sensitive_privacy_metrics.v1",
        "sensitive_attribute_count": len(attributes),
        "conditioned_on_other_sensitive": condition_on_other_sensitive,
        "by_attribute": audits,
        "maximum_delta_disclosure": max(
            result["delta_disclosure"] for result in audits.values()
        ),
        "maximum_categorical_t_closeness": max(
            result["categorical_total_variation_t_closeness"]
            for result in audits.values()
        ),
        "maximum_numeric_emd_t_closeness": max(
            (result.get("numeric_emd_t_closeness", 0.0) for result in audits.values()),
            default=0.0,
        ),
        "raw_values_persisted": False,
    }


def generalize_with_hierarchies(
    source: Path,
    output: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    hierarchies: dict[str, dict[str, list[str]]],
    minimum_k: int,
    max_suppression_fraction: float = 0.0,
) -> dict:
    """Select the least-loss hierarchy levels satisfying k and suppression bound."""
    if minimum_k < 2 or not 0 <= max_suppression_fraction <= 1:
        raise ValueError("invalid privacy bounds")
    if output.exists():
        raise FileExistsError("output already exists")
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [name for name in [*quasi_identifiers, sensitive] if name not in fields]
        if missing:
            raise ValueError(f"missing declared columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("generalization requires records")
    depths = []
    for column in quasi_identifiers:
        mapping = hierarchies.get(column)
        if not mapping or any(row[column] not in mapping for row in rows):
            raise ValueError(f"hierarchy does not cover declared column: {column}")
        lengths = {len(mapping[row[column]]) for row in rows}
        if len(lengths) != 1:
            raise ValueError(f"hierarchy depth must be uniform: {column}")
        depths.append(next(iter(lengths)))

    candidates = []
    for levels in itertools.product(*(range(depth + 1) for depth in depths)):
        transformed = []
        for row in rows:
            item = dict(row)
            for column, level in zip(quasi_identifiers, levels, strict=True):
                if level:
                    item[column] = hierarchies[column][row[column]][level - 1]
            transformed.append(item)
        counts = Counter(tuple(row[name] for name in quasi_identifiers) for row in transformed)
        kept = [
            row
            for row in transformed
            if counts[tuple(row[name] for name in quasi_identifiers)] >= minimum_k
        ]
        suppression = (len(rows) - len(kept)) / len(rows)
        if kept and suppression <= max_suppression_fraction:
            # Prefer utility: fewer suppressed rows, then less total/cell generalization.
            candidates.append(((len(rows) - len(kept), sum(levels), levels), kept))
    if not candidates:
        raise ValueError("no hierarchy selection satisfies privacy and suppression bounds")
    (suppressed, level_cost, levels), selected = min(candidates, key=lambda item: item[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    recomputed = audit_csv(output, quasi_identifiers, sensitive)
    if recomputed["k_anonymity"] < minimum_k:
        output.unlink(missing_ok=True)
        raise RuntimeError("independent post-transform privacy recomputation failed")
    return {
        "schema": "hierarchy_generalization.v1",
        "input_records": len(rows),
        "output_records": len(selected),
        "suppressed_records": suppressed,
        "selected_levels": dict(zip(quasi_identifiers, levels, strict=True)),
        "generalization_level_cost": level_cost,
        "privacy_recomputed": recomputed,
        "utility": {"record_retention": len(selected) / len(rows)},
    }


def locally_generalize_with_hierarchies(
    source: Path,
    output: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    hierarchies: dict[str, dict[str, list[str]]],
    minimum_k: int,
) -> dict:
    """Generalize only unsafe records, preserving already-safe classes."""
    if minimum_k < 2:
        raise ValueError("minimum_k must be at least 2")
    if output.exists():
        raise FileExistsError("output already exists")
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        missing = [name for name in [*quasi_identifiers, sensitive] if name not in fields]
        if missing:
            raise ValueError(f"missing declared columns: {', '.join(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError("local generalization requires records")
    depths = []
    for column in quasi_identifiers:
        mapping = hierarchies.get(column)
        if not mapping or any(row[column] not in mapping for row in rows):
            raise ValueError(f"hierarchy does not cover declared column: {column}")
        lengths = {len(mapping[row[column]]) for row in rows}
        if len(lengths) != 1:
            raise ValueError(f"hierarchy depth must be uniform: {column}")
        depths.append(next(iter(lengths)))
    levels = [[0] * len(quasi_identifiers) for _ in rows]

    def materialize(candidate: list[list[int]]) -> list[dict[str, str]]:
        result = []
        for row, row_levels in zip(rows, candidate, strict=True):
            item = dict(row)
            for column, level in zip(quasi_identifiers, row_levels, strict=True):
                if level:
                    item[column] = hierarchies[column][row[column]][level - 1]
            result.append(item)
        return result

    while True:
        transformed = materialize(levels)
        counts = Counter(tuple(row[name] for name in quasi_identifiers) for row in transformed)
        unsafe = [
            i
            for i, row in enumerate(transformed)
            if counts[tuple(row[n] for n in quasi_identifiers)] < minimum_k
        ]
        if not unsafe:
            break
        candidates = []
        for column_index, depth in enumerate(depths):
            candidate = [list(item) for item in levels]
            changed = False
            for i in unsafe:
                if candidate[i][column_index] < depth:
                    candidate[i][column_index] += 1
                    changed = True
            if changed:
                materialized = materialize(candidate)
                candidate_counts = Counter(
                    tuple(row[n] for n in quasi_identifiers) for row in materialized
                )
                remaining = sum(
                    candidate_counts[tuple(row[n] for n in quasi_identifiers)] < minimum_k
                    for row in materialized
                )
                candidates.append(((remaining, sum(map(sum, candidate)), column_index), candidate))
        if not candidates:
            raise ValueError("local recoding cannot satisfy minimum k with supplied hierarchies")
        levels = min(candidates, key=lambda item: item[0])[1]
    selected = materialize(levels)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)
    recomputed = audit_csv(output, quasi_identifiers, sensitive)
    if recomputed["k_anonymity"] < minimum_k:
        output.unlink(missing_ok=True)
        raise RuntimeError("independent post-transform privacy recomputation failed")
    return {
        "schema": "local_hierarchy_generalization.v1",
        "input_records": len(rows),
        "output_records": len(selected),
        "generalized_cells": sum(level > 0 for item in levels for level in item),
        "privacy_recomputed": recomputed,
        "raw_values_persisted_in_receipt": False,
    }


def microaggregate_and_code(
    source: Path,
    output: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    numeric_columns: list[str],
    minimum_k: int,
    bounds: dict[str, tuple[float | None, float | None]],
) -> dict:
    """Apply authorized top/bottom coding and fixed-size numeric microaggregation."""
    if minimum_k < 2 or not numeric_columns or len(set(numeric_columns)) != len(numeric_columns):
        raise ValueError("invalid microaggregation parameters")
    if not set(numeric_columns) <= set(quasi_identifiers):
        raise ValueError("numeric columns must be declared quasi-identifiers")
    if output.exists():
        raise FileExistsError("output already exists")
    fields, rows = _read_csv(source)
    missing = [name for name in [*quasi_identifiers, sensitive] if name not in fields]
    if missing:
        raise ValueError(f"missing declared columns: {', '.join(missing)}")
    if len(rows) < minimum_k:
        raise ValueError("fewer records than minimum_k")
    coded: list[dict[str, str]] = []
    for row in rows:
        item = dict(row)
        for column in numeric_columns:
            try:
                value = float(row[column])
            except ValueError as error:
                raise ValueError(f"declared numeric column is not numeric: {column}") from error
            lower, upper = bounds.get(column, (None, None))
            if lower is not None and upper is not None and lower > upper:
                raise ValueError(f"invalid coding bounds: {column}")
            item[column] = str(max(lower, value) if lower is not None else value)
            value = float(item[column])
            item[column] = str(min(upper, value) if upper is not None else value)
        coded.append(item)
    coded.sort(key=lambda row: tuple(float(row[name]) for name in numeric_columns))
    clusters = [coded[index : index + minimum_k] for index in range(0, len(coded), minimum_k)]
    if len(clusters) > 1 and len(clusters[-1]) < minimum_k:
        clusters[-2].extend(clusters.pop())
    for cluster in clusters:
        for column in numeric_columns:
            mean = sum(float(row[column]) for row in cluster) / len(cluster)
            rendered = format(mean, ".12g")
            for row in cluster:
                row[column] = rendered
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(coded)
    metrics = audit_csv(output, quasi_identifiers, sensitive)
    if metrics["k_anonymity"] < minimum_k:
        output.unlink(missing_ok=True)
        raise ValueError("post-transform k-anonymity bound unsatisfied")
    return {
        "schema": "microaggregation_and_coding.v1",
        "input_records": len(rows),
        "output_records": len(coded),
        "minimum_k": minimum_k,
        "microaggregated_columns": sorted(numeric_columns),
        "coded_columns": sorted(bounds),
        "privacy_recomputed": metrics,
        "raw_values_persisted_in_receipt": False,
    }


def enforce_advanced_privacy_transform(
    source: Path,
    output: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    hierarchies: dict[str, dict[str, list[str]]],
    *,
    minimum_k: int,
    maximum_alpha: float,
    recursive_l: int,
    maximum_recursive_c: float,
    maximum_beta: float,
    maximum_t: float,
    maximum_numeric_emd_t: float | None = None,
    minimum_entropy_l: float | None = None,
    maximum_delta_disclosure: float | None = None,
    max_suppression_fraction: float = 0.0,
) -> dict:
    """Generalize then fail closed unless all declared advanced models hold."""
    if (
        not 0 <= maximum_alpha <= 1
        or recursive_l < 2
        or min(maximum_recursive_c, maximum_beta, maximum_t) < 0
        or (maximum_numeric_emd_t is not None and maximum_numeric_emd_t < 0)
        or (minimum_entropy_l is not None and minimum_entropy_l < 1)
        or (maximum_delta_disclosure is not None and maximum_delta_disclosure < 0)
    ):
        raise ValueError("invalid advanced privacy bounds")
    transform = generalize_with_hierarchies(
        source,
        output,
        quasi_identifiers,
        sensitive,
        hierarchies,
        minimum_k,
        max_suppression_fraction,
    )
    metrics = transform["privacy_recomputed"]
    recursive = metrics["recursive_c_l_diversity"]["minimum_c_by_l"].get(str(recursive_l))
    violations = []
    if metrics["alpha_k_anonymity"]["maximum_sensitive_frequency"] > maximum_alpha:
        violations.append("alpha_k_anonymity")
    if recursive is None or recursive > maximum_recursive_c:
        violations.append("recursive_c_l_diversity")
    if not _satisfies_enhanced_beta_likeness(output, quasi_identifiers, sensitive, maximum_beta):
        violations.append("enhanced_beta_likeness")
    if minimum_entropy_l is not None and metrics["entropy_effective_l"] < minimum_entropy_l:
        violations.append("entropy_l_diversity")
    if (
        maximum_delta_disclosure is not None
        and metrics["delta_disclosure"] > maximum_delta_disclosure
    ):
        violations.append("delta_disclosure")
    if metrics["categorical_total_variation_t_closeness"] > maximum_t:
        violations.append("categorical_t_closeness")
    if maximum_numeric_emd_t is not None and (
        "numeric_emd_t_closeness" not in metrics
        or metrics["numeric_emd_t_closeness"] > maximum_numeric_emd_t
    ):
        violations.append("numeric_emd_t_closeness")
    if violations:
        output.unlink(missing_ok=True)
        raise ValueError("advanced privacy bounds unsatisfied: " + ", ".join(violations))
    return {
        "schema": "advanced_privacy_transform.v1",
        "bounds": {
            "minimum_k": minimum_k,
            "maximum_alpha": maximum_alpha,
            "recursive_l": recursive_l,
            "maximum_recursive_c": maximum_recursive_c,
            "maximum_beta": maximum_beta,
            "maximum_t": maximum_t,
            "maximum_numeric_emd_t": maximum_numeric_emd_t,
            "minimum_entropy_l": minimum_entropy_l,
            "maximum_delta_disclosure": maximum_delta_disclosure,
        },
        "transformation": transform,
        "raw_values_persisted_in_receipt": False,
    }


def _satisfies_enhanced_beta_likeness(
    path: Path, quasi_identifiers: list[str], sensitive: str, beta: float
) -> bool:
    """Check every relative increase against min(beta, -ln(global probability))."""
    _, rows = _read_csv(path)
    global_counts = Counter(row[sensitive] for row in rows)
    classes: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        classes[tuple(row[name] for name in quasi_identifiers)][row[sensitive]] += 1
    for counts in classes.values():
        local_total = sum(counts.values())
        for value, global_count in global_counts.items():
            global_probability = global_count / len(rows)
            local_probability = counts[value] / local_total
            relative_increase = max(
                0.0, (local_probability - global_probability) / global_probability
            )
            if relative_increase > min(beta, -math.log(global_probability)):
                return False
    return True


def _read_csv(path: Path, *, allow_empty: bool = False) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    if not fields or (not rows and not allow_empty):
        raise ValueError("linkability inputs require headers and records")
    return fields, rows


def _column_distances(rows: list[dict[str, str]], columns: list[str]):
    numeric_ranges: dict[str, tuple[float, float] | None] = {}
    for column in columns:
        try:
            values = [float(row[column]) for row in rows]
        except ValueError:
            numeric_ranges[column] = None
        else:
            numeric_ranges[column] = (min(values), max(values))

    def distance(left: dict[str, str], right: dict[str, str]) -> float:
        total = 0.0
        for column in columns:
            bounds = numeric_ranges[column]
            if bounds is None:
                total += 0.0 if left[column] == right[column] else 1.0
            else:
                low, high = bounds
                span = high - low
                total += abs(float(left[column]) - float(right[column])) / span if span else 0.0
        return total / len(columns)

    return distance


def audit_attribute_inference(
    release: Path,
    evaluation: Path,
    quasi_identifiers: list[str],
    sensitive: str,
    group_by: str | None = None,
    predictor: str = "nearest_neighbor",
) -> dict:
    """Measure sensitive-attribute inference using an authorized predictor."""
    if predictor not in {"nearest_neighbor", "exact_match"}:
        raise ValueError("predictor must be nearest_neighbor or exact_match")
    if not quasi_identifiers or len(set(quasi_identifiers)) != len(quasi_identifiers):
        raise ValueError("quasi_identifiers must be a non-empty unique list")
    if sensitive in quasi_identifiers:
        raise ValueError("sensitive column cannot be a quasi-identifier")
    release_fields, release_rows = _read_csv(release)
    evaluation_fields, evaluation_rows = _read_csv(evaluation)
    declared = [*quasi_identifiers, sensitive, *([group_by] if group_by else [])]
    for label, fields in (("release", release_fields), ("evaluation", evaluation_fields)):
        missing = [name for name in declared if name not in fields]
        if missing:
            raise ValueError(f"{label} missing declared columns: {', '.join(missing)}")
    distance = _column_distances([*release_rows, *evaluation_rows], quasi_identifiers)
    majority = Counter(row[sensitive] for row in release_rows).most_common(1)[0][0]
    def predict_labels(row: dict[str, str]) -> set[str]:
        if predictor == "exact_match":
            return {
                candidate[sensitive]
                for candidate in release_rows
                if all(candidate[column] == row[column] for column in quasi_identifiers)
            }
        scores = [distance(row, candidate) for candidate in release_rows]
        best = min(scores)
        return {
            candidate[sensitive]
            for candidate, score in zip(release_rows, scores, strict=True)
            if math.isclose(score, best)
        }

    inferred = correct = abstentions = baseline_correct = 0
    for row in evaluation_rows:
        labels = predict_labels(row)
        baseline_correct += row[sensitive] == majority
        if len(labels) != 1:
            abstentions += 1
            continue
        inferred += 1
        correct += next(iter(labels)) == row[sensitive]
    accuracy = correct / len(evaluation_rows)
    baseline = baseline_correct / len(evaluation_rows)
    result = {
        "schema": "attribute_inference_risk.v1",
        "evaluation_records": len(evaluation_rows),
        "release_records": len(release_rows),
        "quasi_identifier_count": len(quasi_identifiers),
        "predictor": predictor,
        "inferred_records": inferred,
        "abstentions": abstentions,
        "accuracy": round(accuracy, 12),
        "majority_baseline": round(baseline, 12),
        "excess_over_baseline": round(accuracy - baseline, 12),
        "verdict": "attribute_inference_risk" if accuracy > baseline else "clear",
        "raw_values_persisted": False,
    }
    if group_by:
        grouped: dict[str, list[bool]] = {}
        for row in evaluation_rows:
            labels = predict_labels(row)
            grouped.setdefault(row[group_by], []).append(
                len(labels) == 1 and next(iter(labels)) == row[sensitive]
            )
        accuracies = [sum(outcomes) / len(outcomes) for outcomes in grouped.values()]
        result["group_count"] = len(accuracies)
        result["minimum_group_accuracy"] = round(min(accuracies), 12)
        result["maximum_group_accuracy"] = round(max(accuracies), 12)
        result["group_values_persisted"] = False
    return result


def audit_singling_out(
    path: Path,
    quasi_identifiers: list[str],
    max_predicate_size: int | None = None,
    control: Path | None = None,
) -> dict:
    """Search equality predicates over authorized columns and report aggregate exposure."""
    if not quasi_identifiers or len(set(quasi_identifiers)) != len(quasi_identifiers):
        raise ValueError("quasi_identifiers must be a non-empty unique list")
    if len(quasi_identifiers) > 12:
        raise ValueError("predicate search supports at most 12 quasi-identifiers")
    if max_predicate_size is None:
        max_predicate_size = len(quasi_identifiers)
    if not 1 <= max_predicate_size <= len(quasi_identifiers):
        raise ValueError("max_predicate_size must be between 1 and the quasi-identifier count")
    fields, rows = _read_csv(path)
    missing = [name for name in quasi_identifiers if name not in fields]
    if missing:
        raise ValueError(f"missing declared columns: {', '.join(missing)}")

    exposed: set[int] = set()
    predicate_count = 0
    successful_predicates = 0
    for size in range(1, max_predicate_size + 1):
        for columns in itertools.combinations(quasi_identifiers, size):
            groups: dict[tuple[str, ...], list[int]] = {}
            for index, row in enumerate(rows):
                groups.setdefault(tuple(row[name] for name in columns), []).append(index)
            predicate_count += len(groups)
            for matches in groups.values():
                if len(matches) == 1:
                    successful_predicates += 1
                    exposed.add(matches[0])
    rate = len(exposed) / len(rows)
    baseline = 1 / len(rows)
    control_rate = None
    if control is not None:
        control_fields, control_rows = _read_csv(control)
        missing = [name for name in quasi_identifiers if name not in control_fields]
        if missing:
            raise ValueError(f"control missing declared columns: {', '.join(missing)}")
        control_exposed: set[int] = set()
        for size in range(1, max_predicate_size + 1):
            for columns in itertools.combinations(quasi_identifiers, size):
                groups: dict[tuple[str, ...], list[int]] = {}
                for index, row in enumerate(control_rows):
                    groups.setdefault(tuple(row[name] for name in columns), []).append(index)
                control_exposed.update(
                    matches[0] for matches in groups.values() if len(matches) == 1
                )
        control_rate = len(control_exposed) / len(control_rows)
    z = 1.96
    denominator = 1 + z * z / len(rows)
    center = (rate + z * z / (2 * len(rows))) / denominator
    margin = z * math.sqrt(
        rate * (1 - rate) / len(rows) + z * z / (4 * len(rows) ** 2)
    ) / denominator
    comparison_rate = baseline if control_rate is None else control_rate
    return {
        "schema": "singling_out_risk.v3",
        "records": len(rows),
        "quasi_identifier_count": len(quasi_identifiers),
        "max_predicate_size": max_predicate_size,
        "predicates_evaluated": predicate_count,
        "successful_predicates": successful_predicates,
        "unique_records": len(exposed),
        "singling_out_rate": round(rate, 12),
        "random_baseline": round(baseline, 12),
        "excess_over_baseline": round(rate - baseline, 12),
        "control_singling_out_rate": None if control_rate is None else round(control_rate, 12),
        "control_adjusted_excess": None if control_rate is None else round(rate - control_rate, 12),
        "risk_threshold_kind": "random_baseline" if control_rate is None else "control_data",
        "confidence_interval_95": [
            round(max(0.0, center - margin), 12),
            round(min(1.0, center + margin), 12),
        ],
        "verdict": "singling_out_risk" if rate > comparison_rate else "clear",
        "raw_values_persisted": False,
    }


def audit_two_view_linkability(
    release: Path,
    auxiliary_a: Path,
    auxiliary_b: Path,
    subject_id: str,
    columns_a: list[str],
    columns_b: list[str],
    control: Path | None = None,
) -> dict:
    """Measure two-view nearest-neighbor linkage without persisting row values.

    Auxiliary views are operator-authorized evaluation data. Each must contain a
    unique subject identifier, while the release must not contain that identifier.
    Tied nearest neighbors abstain rather than being counted as successful links.
    """
    if (
        not columns_a
        or not columns_b
        or len(set(columns_a)) != len(columns_a)
        or len(set(columns_b)) != len(columns_b)
    ):
        raise ValueError("each auxiliary view requires unique declared columns")
    release_fields, release_rows = _read_csv(release)
    fields_a, rows_a = _read_csv(auxiliary_a)
    fields_b, rows_b = _read_csv(auxiliary_b)
    if subject_id in release_fields:
        raise ValueError("subject identifier must not be present in release")
    for label, fields, columns in (("A", fields_a, columns_a), ("B", fields_b, columns_b)):
        missing = [name for name in [subject_id, *columns] if name not in fields]
        if missing:
            raise ValueError(f"missing declared columns in view {label}: {', '.join(missing)}")
        release_missing = [name for name in columns if name not in release_fields]
        if release_missing:
            raise ValueError(f"release missing view {label} columns: {', '.join(release_missing)}")
    by_id_a = {row[subject_id]: row for row in rows_a}
    by_id_b = {row[subject_id]: row for row in rows_b}
    if len(by_id_a) != len(rows_a) or len(by_id_b) != len(rows_b) or set(by_id_a) != set(by_id_b):
        raise ValueError("auxiliary views require identical unique subject identifiers")

    distance_a = _column_distances([*release_rows, *rows_a], columns_a)
    distance_b = _column_distances([*release_rows, *rows_b], columns_b)

    def nearest(row: dict[str, str], distance, candidates: list[dict[str, str]]) -> int | None:
        scores = [distance(row, candidate) for candidate in candidates]
        best = min(scores)
        winners = [index for index, score in enumerate(scores) if math.isclose(score, best)]
        return winners[0] if len(winners) == 1 else None

    def attack(candidates, distance_left, distance_right) -> tuple[int, int, float]:
        successes = 0
        abstentions = 0
        for identifier in sorted(by_id_a):
            left = nearest(by_id_a[identifier], distance_left, candidates)
            right = nearest(by_id_b[identifier], distance_right, candidates)
            if left is None or right is None:
                abstentions += 1
            elif left == right:
                successes += 1
        return successes, abstentions, successes / len(by_id_a)

    successes, abstentions, rate = attack(release_rows, distance_a, distance_b)
    total = len(by_id_a)
    baseline = 1 / len(release_rows)
    control_rate = None
    if control is not None:
        control_fields, control_rows = _read_csv(control)
        missing = [name for name in [*columns_a, *columns_b] if name not in control_fields]
        if missing:
            raise ValueError(f"control missing declared columns: {', '.join(missing)}")
        if subject_id in control_fields:
            raise ValueError("subject identifier must not be present in control")
        control_distance_a = _column_distances([*control_rows, *rows_a], columns_a)
        control_distance_b = _column_distances([*control_rows, *rows_b], columns_b)
        _, _, control_rate = attack(control_rows, control_distance_a, control_distance_b)
    z = 1.96
    denominator = 1 + z * z / total
    center = (rate + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / denominator
    comparison_rate = baseline if control_rate is None else control_rate
    return {
        "schema": "two_view_linkability.v1",
        "evaluated_subjects": total,
        "release_records": len(release_rows),
        "successful_links": successes,
        "abstentions": abstentions,
        "linkability_rate": round(rate, 12),
        "random_baseline": round(baseline, 12),
        "excess_over_baseline": round(rate - baseline, 12),
        "control_linkability_rate": None if control_rate is None else round(control_rate, 12),
        "control_adjusted_excess": None if control_rate is None else round(rate - control_rate, 12),
        "risk_threshold_kind": "random_baseline" if control_rate is None else "control_data",
        "confidence_interval_95": [
            round(max(0.0, center - margin), 12),
            round(min(1.0, center + margin), 12),
        ],
        "verdict": "linkage_risk" if rate > comparison_rate else "clear",
        "raw_values_persisted": False,
    }


def suppress_small_classes(
    source: Path, output: Path, quasi_identifiers: list[str], minimum_k: int
) -> dict:
    """Write a CSV with records in classes smaller than ``minimum_k`` removed."""
    if minimum_k < 2:
        raise ValueError("minimum_k must be at least 2")
    if output.exists():
        raise FileExistsError("output already exists")
    with source.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if any(name not in fields for name in quasi_identifiers):
            raise ValueError("missing declared quasi-identifier column")
        rows = list(reader)
    counts = Counter(tuple(row[name] for name in quasi_identifiers) for row in rows)
    kept = [
        row for row in rows if counts[tuple(row[name] for name in quasi_identifiers)] >= minimum_k
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)
    return {
        "input_records": len(rows),
        "output_records": len(kept),
        "suppressed_records": len(rows) - len(kept),
        "minimum_k": minimum_k,
    }
