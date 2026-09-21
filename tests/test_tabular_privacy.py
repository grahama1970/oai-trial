import json
from pathlib import Path

import pytest

import anonymization_trial.tabular_privacy as tabular_privacy

from anonymization_trial.tabular_privacy import (
    audit_attribute_inference,
    audit_csv,
    audit_delta_presence,
    audit_multiple_sensitive_attributes,
    audit_population_k_map,
    audit_population_reidentification,
    audit_singling_out,
    audit_two_view_linkability,
    enforce_advanced_privacy_transform,
    generalize_with_hierarchies,
    locally_generalize_with_hierarchies,
    microaggregate_and_code,
    release_dp_count,
    release_dp_counts,
    release_dp_counts_persistent,
    release_dp_synthetic_histogram,
    release_dp_synthetic_histogram_persistent,
    suppress_small_classes,
)


def _csv(path: Path) -> Path:
    path.write_text(
        "zip,age,condition\n10001,30,A\n10001,30,B\n20002,40,A\n20002,40,A\n",
        encoding="utf-8",
    )
    return path


def test_local_recoding_preserves_safe_classes_and_recomputes_k(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    output = tmp_path / "release.csv"
    source.write_text(
        "zip,condition\n10001,A\n10001,B\n20001,A\n20002,B\n",
        encoding="utf-8",
    )

    result = locally_generalize_with_hierarchies(
        source,
        output,
        ["zip"],
        "condition",
        {"zip": {"10001": ["100**", "*****"], "20001": ["200**", "*****"], "20002": ["200**", "*****"]}},
        2,
    )

    assert output.read_text(encoding="utf-8").count("10001") == 2
    assert output.read_text(encoding="utf-8").count("200**") == 2
    assert result["generalized_cells"] == 2
    assert result["privacy_recomputed"]["k_anonymity"] == 2
    assert result["raw_values_persisted_in_receipt"] is False


def _randbelow(*values: int):
    iterator = iter(values)

    def draw(limit: int) -> int:
        value = next(iterator)
        assert 0 <= value < limit
        return value

    return draw


def test_dp_count_uses_exact_geometric_noise_without_persisting_predicate(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\nA\nB\n", encoding="utf-8")

    result = release_dp_count(
        source, "condition", "A", "0.7", random_below=_randbelow(1, 1)
    )

    assert result == {
        "schema": "differentially_private_count.v1",
        "mechanism": "exact_two_sided_geometric_p_half",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound": 0.7,
        "adjacency": "add_remove_one_record",
        "epsilon": 0.7,
        "sensitivity": 1,
        "noisy_count": 3,
        "clamped_to_nonnegative": True,
        "composition": "single_query_only",
        "cryptographic_randomness": False,
        "raw_values_persisted": False,
    }
    assert "condition" not in str(result) and "A" not in str(result)


def test_dp_count_accepts_header_only_dataset_for_add_remove_adjacency(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    singleton = tmp_path / "singleton.csv"
    empty.write_text("condition\n", encoding="utf-8")
    singleton.write_text("condition\nA\n", encoding="utf-8")

    empty_result = release_dp_count(empty, "condition", "A", "0.7", random_below=_randbelow(0))
    singleton_result = release_dp_count(singleton, "condition", "A", "0.7", random_below=_randbelow(0))

    assert empty_result["noisy_count"] == 0
    assert singleton_result["noisy_count"] == 1
    assert empty_result["adjacency"] == singleton_result["adjacency"] == "add_remove_one_record"


def test_dp_count_rejects_invalid_epsilon(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\n", encoding="utf-8")
    with pytest.raises(ValueError, match="epsilon"):
        release_dp_count(source, "condition", "A", 0)


def test_dp_count_batch_accounts_for_composed_budget_without_predicates(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\nA\nB\n", encoding="utf-8")

    result = release_dp_counts(
        source,
        [
            {"column": "condition", "equals": "A", "epsilon": "0.7"},
            {"column": "condition", "equals": "B", "epsilon": "0.7"},
        ],
        "1.4",
        random_below=_randbelow(1, 1, 2, 1),
    )

    assert result == {
        "schema": "differentially_private_count_batch.v1",
        "mechanism": "exact_two_sided_geometric_p_half",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound_per_query": 0.7,
        "adjacency": "add_remove_one_record",
        "composition": "basic_sequential_composition",
        "query_count": 2,
        "total_epsilon": 1.4,
        "maximum_epsilon": 1.4,
        "remaining_epsilon": 0.0,
        "noisy_counts": [3, 0],
        "cryptographic_randomness": False,
        "raw_values_persisted": False,
    }
    assert "condition" not in str(result) and "A" not in str(result) and "B" not in str(result)


def test_dp_count_batch_accepts_header_only_dataset_for_add_remove_adjacency(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\n", encoding="utf-8")

    result = release_dp_counts(
        source,
        [
            {"column": "condition", "equals": "A", "epsilon": "0.7"},
            {"column": "condition", "equals": "B", "epsilon": "0.7"},
        ],
        "1.4",
        random_below=_randbelow(0, 0),
    )

    assert result["noisy_counts"] == [0, 0]
    assert result["adjacency"] == "add_remove_one_record"
    assert result["query_count"] == 2


def test_dp_count_batch_rejects_budget_overspend(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds"):
        release_dp_counts(
            source,
            [
                {"column": "condition", "equals": "A", "epsilon": "0.7"},
                {"column": "condition", "equals": "B", "epsilon": "0.7"},
            ],
            "1.0",
        )


def test_dp_count_batch_rejects_epsilon_hidden_below_decimal_precision(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\n", encoding="utf-8")
    with pytest.raises(ValueError, match="query epsilon"):
        release_dp_counts(
            source,
            [
                {"column": "condition", "equals": "A", "epsilon": "1.0"},
                {"column": "condition", "equals": "B", "epsilon": "1e-30"},
            ],
            "1.0",
        )


def test_dp_count_persistent_budget_survives_invocations_without_predicates(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    ledger = tmp_path / "budget.json"
    source.write_text("condition\nA\nB\n", encoding="utf-8")
    query = [{"column": "condition", "equals": "A", "epsilon": "0.7"}]

    first = release_dp_counts_persistent(
        source, query, "1.4", ledger, "release-authorization", random_below=_randbelow(0)
    )
    second = release_dp_counts_persistent(
        source, query, "1.4", ledger, "release-authorization", random_below=_randbelow(0)
    )

    assert first["cumulative_epsilon"] == 0.7
    assert second["cumulative_epsilon"] == 1.4
    assert second["persistent_remaining_epsilon"] == 0.0
    assert second["budget_ledger_contains_predicates"] is False
    persisted = ledger.read_text(encoding="utf-8")
    assert "condition" not in persisted and "release-authorization" not in persisted
    with pytest.raises(ValueError, match="persistent composed epsilon exceeds"):
        release_dp_counts_persistent(source, query, "1.4", ledger, "release-authorization")


def test_dp_count_rejects_domain_that_can_overflow_noise(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text("condition\nA\n", encoding="utf-8")
    with pytest.raises(ValueError, match="between"):
        release_dp_count(source, "condition", "A", "1e-320")


def test_dp_synthetic_histogram_writes_multidimensional_release_without_value_receipt(
    tmp_path: Path,
) -> None:
    source = tmp_path / "people.csv"
    output = tmp_path / "synthetic.csv"
    source.write_text(
        "region,condition\nurban,A\nurban,A\nrural,B\n",
        encoding="utf-8",
    )

    result = release_dp_synthetic_histogram(
        source,
        output,
        ["region", "condition"],
        {"region": ["urban", "rural"], "condition": ["A", "B"]},
        "0.7",
        random_below=_randbelow(0, 0, 0, 0),
    )

    assert result == {
        "schema": "differentially_private_synthetic_histogram.v1",
        "mechanism": "exact_two_sided_geometric_p_half_multidimensional_histogram",
        "privacy_guarantee": "pure_epsilon_differential_privacy",
        "formal_epsilon_upper_bound": 0.7,
        "adjacency": "add_remove_one_record",
        "epsilon": 0.7,
        "sensitivity": 1,
        "composition": "histogram_parallel_cells_one_record_one_cell",
        "dimension_count": 2,
        "domain_cell_count": 4,
        "domain_sizes": [2, 2],
        "source_records": 3,
        "synthetic_records": 3,
        "cryptographic_randomness": False,
        "receipt_contains_domain_values": False,
        "raw_values_persisted": False,
    }
    assert output.read_text(encoding="utf-8") == (
        "region,condition\nurban,A\nurban,A\nrural,B\n"
    )
    assert "urban" not in str(result) and "A" not in str(result)


def test_dp_synthetic_histogram_accepts_header_only_dataset_for_add_remove_adjacency(
    tmp_path: Path,
) -> None:
    empty = tmp_path / "empty.csv"
    singleton = tmp_path / "singleton.csv"
    empty_output = tmp_path / "empty.synthetic.csv"
    singleton_output = tmp_path / "singleton.synthetic.csv"
    empty.write_text("region,condition\n", encoding="utf-8")
    singleton.write_text("region,condition\nurban,A\n", encoding="utf-8")
    domains = {"region": ["urban", "rural"], "condition": ["A", "B"]}

    empty_result = release_dp_synthetic_histogram(
        empty,
        empty_output,
        ["region", "condition"],
        domains,
        "0.7",
        random_below=_randbelow(0, 0, 0, 0),
    )
    singleton_result = release_dp_synthetic_histogram(
        singleton,
        singleton_output,
        ["region", "condition"],
        domains,
        "0.7",
        random_below=_randbelow(0, 0, 0, 0),
    )

    assert empty_result["synthetic_records"] == 0
    assert singleton_result["synthetic_records"] == 1
    assert empty_output.read_text(encoding="utf-8") == "region,condition\n"
    assert singleton_output.read_text(encoding="utf-8") == "region,condition\nurban,A\n"


def test_dp_synthetic_histogram_persistent_budget_composes_invocations(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    first_output = tmp_path / "first.csv"
    second_output = tmp_path / "second.csv"
    ledger = tmp_path / "budget.json"
    source.write_text("region,condition\nurban,A\n", encoding="utf-8")
    domains = {"region": ["urban", "rural"], "condition": ["A", "B"]}

    first = release_dp_synthetic_histogram_persistent(
        source,
        first_output,
        ["region", "condition"],
        domains,
        "0.7",
        "1.4",
        ledger,
        "release-authorization",
        random_below=_randbelow(0, 0, 0, 0),
    )
    second = release_dp_synthetic_histogram_persistent(
        source,
        second_output,
        ["region", "condition"],
        domains,
        "0.7",
        "1.4",
        ledger,
        "release-authorization",
        random_below=_randbelow(0, 0, 0, 0),
    )

    assert first["schema"] == "differentially_private_synthetic_histogram_persistent.v1"
    assert first["cumulative_epsilon"] == 0.7
    assert second["cumulative_epsilon"] == 1.4
    assert second["persistent_remaining_epsilon"] == 0.0
    assert second["budget_ledger_contains_domain_values"] is False
    assert second["budget_ledger_contains_raw_values"] is False
    persisted = ledger.read_text(encoding="utf-8")
    assert "urban" not in persisted and "release-authorization" not in persisted
    with pytest.raises(ValueError, match="persistent composed epsilon exceeds"):
        release_dp_synthetic_histogram_persistent(
            source,
            tmp_path / "third.csv",
            ["region", "condition"],
            domains,
            "0.7",
            "1.4",
            ledger,
            "release-authorization",
        )


def test_dp_synthetic_histogram_persistent_spends_before_lower_level_publish_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "people.csv"
    output = tmp_path / "synthetic.csv"
    ledger = tmp_path / "budget.json"
    source.write_text("region,condition\nurban,A\n", encoding="utf-8")
    original_writer = tabular_privacy.csv.DictWriter

    class FailingWriter:
        def __init__(self, *args, **kwargs):
            self._delegate = original_writer(*args, **kwargs)

        def writeheader(self):
            return self._delegate.writeheader()

        def writerows(self, rows):
            raise OSError("simulated persistent write failure")

    monkeypatch.setattr(tabular_privacy.csv, "DictWriter", FailingWriter)

    with pytest.raises(OSError, match="simulated persistent write failure"):
        release_dp_synthetic_histogram_persistent(
            source,
            output,
            ["region", "condition"],
            {"region": ["urban", "rural"], "condition": ["A", "B"]},
            "0.7",
            "0.7",
            ledger,
            "release-authorization",
            random_below=_randbelow(0, 0, 0, 0),
        )

    assert not output.exists()
    persisted = json.loads(ledger.read_text(encoding="utf-8"))
    assert persisted["spent_numerator"] == 7
    assert persisted["spent_denominator"] == 10

    monkeypatch.setattr(tabular_privacy.csv, "DictWriter", original_writer)
    with pytest.raises(ValueError, match="persistent composed epsilon exceeds"):
        release_dp_synthetic_histogram_persistent(
            source,
            output,
            ["region", "condition"],
            {"region": ["urban", "rural"], "condition": ["A", "B"]},
            "0.7",
            "0.7",
            ledger,
            "release-authorization",
            random_below=_randbelow(0, 0, 0, 0),
        )
    assert not output.exists()


def test_dp_synthetic_histogram_cleans_partial_output_when_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "people.csv"
    output = tmp_path / "synthetic.csv"
    source.write_text("region,condition\nurban,A\n", encoding="utf-8")
    original_writer = tabular_privacy.csv.DictWriter

    class FailingWriter:
        def __init__(self, *args, **kwargs):
            self._delegate = original_writer(*args, **kwargs)

        def writeheader(self):
            return self._delegate.writeheader()

        def writerows(self, rows):
            raise OSError("simulated write failure")

    monkeypatch.setattr(tabular_privacy.csv, "DictWriter", FailingWriter)

    with pytest.raises(OSError, match="simulated write failure"):
        release_dp_synthetic_histogram(
            source,
            output,
            ["region", "condition"],
            {"region": ["urban", "rural"], "condition": ["A", "B"]},
            "0.7",
            random_below=_randbelow(0, 0, 0, 0),
        )
    assert not output.exists()


def test_dp_synthetic_histogram_rejects_values_outside_public_domain(
    tmp_path: Path,
) -> None:
    source = tmp_path / "people.csv"
    source.write_text("region,condition\nsecret,A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="outside the declared public domain"):
        release_dp_synthetic_histogram(
            source,
            tmp_path / "synthetic.csv",
            ["region", "condition"],
            {"region": ["urban", "rural"], "condition": ["A", "B"]},
            "0.7",
        )


def test_delta_presence_reports_aggregate_bounds_without_values(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("zip,age\na,20\na,20\nb,30\n", encoding="utf-8")
    population.write_text("zip,age\na,20\na,20\na,20\na,20\nb,30\nb,30\n", encoding="utf-8")

    result = audit_delta_presence(release, population, ["zip", "age"])

    assert result == {
        "schema": "delta_presence_metrics.v1",
        "release_records": 3,
        "population_records": 6,
        "quasi_identifier_count": 2,
        "equivalence_classes": 2,
        "minimum_delta_presence": 0.5,
        "maximum_delta_presence": 0.5,
        "raw_values_persisted": False,
    }
    assert "20" not in str(result) and "30" not in str(result)


def test_delta_presence_rejects_release_outside_population(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("group\na\na\n", encoding="utf-8")
    population.write_text("group\na\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a QI-class subset"):
        audit_delta_presence(release, population, ["group"])


def test_population_reidentification_reports_aggregate_risk_without_qi_values(
    tmp_path: Path,
) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("zip,age\na,20\na,20\nb,30\n", encoding="utf-8")
    population.write_text(
        "zip,age\na,20\na,20\na,20\na,20\nb,30\nc,40\n", encoding="utf-8"
    )

    result = audit_population_reidentification(
        release, population, ["zip", "age"]
    )

    assert result == {
        "schema": "population_reidentification_risk.v1",
        "release_records": 3,
        "population_records": 6,
        "quasi_identifier_count": 2,
        "equivalence_classes": 2,
        "sample_unique_records": 1,
        "population_unique_records": 1,
        "sample_uniqueness_rate": 0.333333333333,
        "population_uniqueness_rate": 0.333333333333,
        "maximum_prosecutor_risk": 1.0,
        "maximum_journalist_risk": 1.0,
        "marketer_success_rate": 0.5,
        "raw_values_persisted": False,
    }
    assert "20" not in str(result) and "30" not in str(result)


def test_population_k_map_reports_bounds_without_qi_values(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("zip,age\na,20\na,20\nb,30\n", encoding="utf-8")
    population.write_text(
        "zip,age\na,20\na,20\na,20\na,20\nb,30\nb,30\n", encoding="utf-8"
    )

    result = audit_population_k_map(release, population, ["zip", "age"], 2)

    assert result == {
        "schema": "population_k_map.v1",
        "release_records": 3,
        "population_records": 6,
        "quasi_identifier_count": 2,
        "release_equivalence_classes": 2,
        "minimum_k": 2,
        "minimum_population_class_size": 2,
        "maximum_population_class_size": 4,
        "violating_release_classes": 0,
        "absent_release_classes": 0,
        "k_map_satisfied": True,
        "verdict": "pass",
        "receipt_contains_qi_values": False,
        "raw_values_persisted": False,
    }
    assert "20" not in str(result) and "30" not in str(result)


def test_population_k_map_flags_absent_or_small_population_classes(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("zip,age\na,20\nb,30\n", encoding="utf-8")
    population.write_text("zip,age\na,20\n", encoding="utf-8")

    result = audit_population_k_map(release, population, ["zip", "age"], 2)

    assert result["k_map_satisfied"] is False
    assert result["verdict"] == "k_map_violation"
    assert result["violating_release_classes"] == 2
    assert result["absent_release_classes"] == 1
    assert "20" not in json.dumps(result) and "30" not in json.dumps(result)


@pytest.mark.parametrize(
    ("release_text", "population_text", "message"),
    [
        ("zip,zip\na,20\n", "zip,age\na,20\na,20\n", "headers must be unique"),
        ("zip,age\na\n", "zip,age\na,20\na,20\n", "exactly the declared header"),
        ("zip,age\na,\n", "zip,age\na,20\na,20\n", "missing quasi-identifier cell"),
        ("zip,age\na,20\n", "zip,age\na\na,20\n", "exactly the declared header"),
        ("zip,age\na,20\n", "zip,age\na,\na,20\n", "missing quasi-identifier cell"),
    ],
)
def test_population_k_map_rejects_ambiguous_or_incomplete_csv(
    tmp_path: Path, release_text: str, population_text: str, message: str
) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text(release_text, encoding="utf-8")
    population.write_text(population_text, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        audit_population_k_map(release, population, ["zip", "age"], 2)


def test_population_reidentification_rejects_non_subset(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    population = tmp_path / "population.csv"
    release.write_text("group\na\na\n", encoding="utf-8")
    population.write_text("group\na\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a QI-class subset"):
        audit_population_reidentification(release, population, ["group"])


def test_multiple_sensitive_attributes_report_delta_and_t_without_values(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text(
        "group,condition,income\na,A,10\na,B,20\nb,A,10\nb,A,30\n",
        encoding="utf-8",
    )
    result = audit_multiple_sensitive_attributes(
        source, ["group"], ["condition", "income"]
    )
    assert result["schema"] == "multiple_sensitive_privacy_metrics.v1"
    assert result["conditioned_on_other_sensitive"] is False
    assert set(result["by_attribute"]) == {"condition", "income"}
    assert result["maximum_delta_disclosure"] == max(
        item["delta_disclosure"] for item in result["by_attribute"].values()
    )
    assert result["maximum_categorical_t_closeness"] == 0.25
    assert result["maximum_numeric_emd_t_closeness"] == 0.125
    assert result["raw_values_persisted"] is False
    assert all("distribution" not in item for item in result["by_attribute"].values())


def test_multiple_sensitive_attributes_support_conditioned_pycanon_mode(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    source.write_text(
        "group,condition,income\na,A,10\na,B,20\nb,A,10\nb,B,20\n",
        encoding="utf-8",
    )

    independent = audit_multiple_sensitive_attributes(
        source, ["group"], ["condition", "income"]
    )
    conditioned = audit_multiple_sensitive_attributes(
        source,
        ["group"],
        ["condition", "income"],
        condition_on_other_sensitive=True,
    )

    assert conditioned["conditioned_on_other_sensitive"] is True
    assert conditioned["sensitive_attribute_count"] == 2
    assert set(conditioned["by_attribute"]) == {"condition", "income"}
    assert independent["by_attribute"]["condition"]["k_anonymity"] == 2
    assert all(
        audit["k_anonymity"] == 1
        and audit["quasi_identifier_count"] == 2
        and audit["equivalence_classes"] == 4
        for audit in conditioned["by_attribute"].values()
    )
    assert conditioned["by_attribute"]["condition"][
        "categorical_total_variation_t_closeness"
    ] == 0.5
    assert conditioned["by_attribute"]["income"]["numeric_emd_t_closeness"] == 0.5
    assert conditioned["maximum_categorical_t_closeness"] == 0.5
    assert conditioned["maximum_numeric_emd_t_closeness"] == 0.5
    assert conditioned["raw_values_persisted"] is False
    assert "A" not in str(conditioned) and "10" not in str(conditioned)


def test_multiple_sensitive_attributes_reject_overlap(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must not also be quasi-identifiers"):
        audit_multiple_sensitive_attributes(
            _csv(tmp_path / "people.csv"), ["zip"], ["zip", "condition"]
        )


def test_declared_qi_metrics_are_exact_and_aggregate(tmp_path: Path) -> None:
    result = audit_csv(_csv(tmp_path / "people.csv"), ["zip", "age"], "condition")
    assert result["schema"] == "tabular_privacy_metrics.v2"
    assert result["records"] == result["raw_records"] == 4
    assert result["suppressed_records"] == 0
    assert result["equivalence_classes"] == 2
    assert result["average_equivalence_class_size"] == 1.0
    assert result["discernibility_metric"] == 8
    assert result["classification_metric"] == 0.25
    assert result["average_reidentification_risk"] == 0.5
    assert result["maximum_reidentification_risk"] == 0.5
    assert result["equivalence_class_statistics"] == {
        "count": 2, "minimum_size": 2, "maximum_size": 2, "mean_size": 2.0, "median_size": 2.0
    }
    assert result["k_anonymity"] == 2
    assert result["l_diversity"] == 1
    assert result["raw_values_persisted"] is False


def test_advanced_privacy_models_use_named_conventions_and_boundaries(tmp_path: Path) -> None:
    path = tmp_path / "advanced.csv"
    path.write_text(
        "group,condition\na,A\na,A\na,B\na,C\nb,A\nb,B\nb,C\nb,C\n",
        encoding="utf-8",
    )
    result = audit_csv(path, ["group"], "condition")
    assert result["alpha_k_anonymity"] == {"k": 4, "maximum_sensitive_frequency": 0.5}
    assert result["recursive_c_l_diversity"]["minimum_c_by_l"] == {"2": 1.0, "3": 2.0}
    assert result["entropy_logarithm"] == "natural"
    assert result["entropy_l_diversity"] == 2
    assert result["entropy_effective_l"] == pytest.approx(2.828427124746, abs=1e-12)
    assert result["basic_beta_likeness"] == pytest.approx(1 / 3)
    assert result["enhanced_beta_likeness"] == pytest.approx(1 / 3)
    assert result["categorical_total_variation_t_closeness"] == pytest.approx(0.125)
    assert result["average_equivalence_class_size"] == 1.0
    assert result["discernibility_metric"] == 32


def test_advanced_transform_rejects_uncapped_beta_increase(tmp_path: Path) -> None:
    source = tmp_path / "people.csv"
    output = tmp_path / "release.csv"
    source.write_text(
        "group,condition\n"
        + "".join(["a,A\n"] * 99 + ["a,B\n", "b,A\n"] + ["b,B\n"] * 24),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="enhanced_beta_likeness"):
        enforce_advanced_privacy_transform(
            source,
            output,
            ["group"],
            "condition",
            {"group": {"a": [], "b": []}},
            minimum_k=2,
            maximum_alpha=1,
            recursive_l=2,
            maximum_recursive_c=100,
            maximum_beta=2,
            maximum_t=1,
        )

    assert not output.exists()
    metrics = audit_csv(source, ["group"], "condition")
    assert metrics["enhanced_beta_likeness"] < 2


def test_entropy_l_diversity_uses_the_weakest_equivalence_class(tmp_path: Path) -> None:
    path = tmp_path / "balanced.csv"
    path.write_text(
        "group,condition\na,A\na,B\nb,A\nb,B\n",
        encoding="utf-8",
    )
    result = audit_csv(path, ["group"], "condition")
    assert result["entropy_l_diversity"] == 2
    assert "A" not in str(result)
    assert "B" not in str(result)


def test_attribute_inference_reports_excess_without_raw_values(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    evaluation = tmp_path / "evaluation.csv"
    release.write_text("age,city,condition\n20,A,x\n40,B,y\n60,C,y\n", encoding="utf-8")
    evaluation.write_text("age,city,condition\n21,A,x\n39,B,y\n", encoding="utf-8")

    result = audit_attribute_inference(release, evaluation, ["age", "city"], "condition")

    assert result == {
        "schema": "attribute_inference_risk.v1",
        "evaluation_records": 2,
        "release_records": 3,
        "quasi_identifier_count": 2,
        "predictor": "nearest_neighbor",
        "inferred_records": 2,
        "abstentions": 0,
        "accuracy": 1.0,
        "majority_baseline": 0.5,
        "excess_over_baseline": 0.5,
        "verdict": "attribute_inference_risk",
        "raw_values_persisted": False,
    }
    assert "condition" not in str(result)
    with pytest.raises(ValueError, match="missing declared columns"):
        audit_attribute_inference(release, release, ["unknown"], "condition")


def test_attribute_inference_supports_authorized_exact_match_predictor(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    evaluation = tmp_path / "evaluation.csv"
    release.write_text("age,condition\n20,x\n40,y\n", encoding="utf-8")
    evaluation.write_text("age,condition\n20,x\n41,y\n", encoding="utf-8")

    result = audit_attribute_inference(
        release, evaluation, ["age"], "condition", predictor="exact_match"
    )

    assert result["predictor"] == "exact_match"
    assert result["inferred_records"] == 1
    assert result["abstentions"] == 1
    assert result["raw_values_persisted"] is False
    with pytest.raises(ValueError, match="predictor must"):
        audit_attribute_inference(release, evaluation, ["age"], "condition", predictor="plugin")


def test_attribute_inference_reports_group_bounds_without_group_values(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    evaluation = tmp_path / "evaluation.csv"
    release.write_text(
        "age,condition,cohort\n20,x,A\n40,y,B\n60,y,A\n", encoding="utf-8"
    )
    evaluation.write_text(
        "age,condition,cohort\n21,x,A\n39,y,A\n59,x,B\n", encoding="utf-8"
    )

    result = audit_attribute_inference(
        release, evaluation, ["age"], "condition", group_by="cohort"
    )

    assert result["group_count"] == 2
    assert result["minimum_group_accuracy"] == 0.0
    assert result["maximum_group_accuracy"] == 1.0
    assert result["group_values_persisted"] is False
    assert "cohort" not in str(result) and "A" not in str(result) and "B" not in str(result)


def test_two_view_linkability_reports_attack_rate_without_raw_values(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    view_a = tmp_path / "view-a.csv"
    view_b = tmp_path / "view-b.csv"
    release.write_text(
        "age,city,income,condition\n20,A,10,x\n40,B,30,y\n60,C,50,z\n",
        encoding="utf-8",
    )
    view_a.write_text("id,age,city\np1,20,A\np2,40,B\np3,60,C\n", encoding="utf-8")
    view_b.write_text("id,income,condition\np1,10,x\np2,30,y\np3,50,z\n", encoding="utf-8")

    result = audit_two_view_linkability(
        release, view_a, view_b, "id", ["age", "city"], ["income", "condition"]
    )

    assert result["schema"] == "two_view_linkability.v1"
    assert result["successful_links"] == 3
    assert result["linkability_rate"] == 1.0
    assert result["random_baseline"] == pytest.approx(1 / 3)
    assert result["verdict"] == "linkage_risk"
    assert result["raw_values_persisted"] is False
    assert "p1" not in str(result)


def test_two_view_linkability_uses_optional_control_data(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    control = tmp_path / "control.csv"
    view_a = tmp_path / "view-a.csv"
    view_b = tmp_path / "view-b.csv"
    release.write_text("age,city,income\n20,A,10\n40,B,30\n", encoding="utf-8")
    control.write_text("age,city,income\n20,Z,30\n40,Z,10\n", encoding="utf-8")
    view_a.write_text("id,age,city\np1,20,A\np2,40,B\n", encoding="utf-8")
    view_b.write_text("id,income\np1,10\np2,30\n", encoding="utf-8")

    result = audit_two_view_linkability(
        release, view_a, view_b, "id", ["age", "city"], ["income"], control
    )

    assert result["linkability_rate"] == 1.0
    assert result["control_linkability_rate"] == 0.0
    assert result["control_adjusted_excess"] == 1.0
    assert result["risk_threshold_kind"] == "control_data"
    assert result["verdict"] == "linkage_risk"
    assert "p1" not in str(result)


def test_two_view_linkability_control_calibrates_verdict(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    control = tmp_path / "control.csv"
    view_a = tmp_path / "view-a.csv"
    view_b = tmp_path / "view-b.csv"
    rows = "age,income\n20,10\n40,30\n"
    release.write_text(rows, encoding="utf-8")
    control.write_text(rows, encoding="utf-8")
    view_a.write_text("id,age\np1,20\np2,40\n", encoding="utf-8")
    view_b.write_text("id,income\np1,10\np2,30\n", encoding="utf-8")

    result = audit_two_view_linkability(
        release, view_a, view_b, "id", ["age"], ["income"], control
    )

    assert result["linkability_rate"] == 1.0
    assert result["control_linkability_rate"] == 1.0
    assert result["control_adjusted_excess"] == 0.0
    assert result["risk_threshold_kind"] == "control_data"
    assert result["verdict"] == "clear"


def test_two_view_linkability_fails_closed_on_subject_id_in_release(tmp_path: Path) -> None:
    release = tmp_path / "release.csv"
    view_a = tmp_path / "view-a.csv"
    view_b = tmp_path / "view-b.csv"
    release.write_text("id,age,income\np1,20,10\n", encoding="utf-8")
    view_a.write_text("id,age\np1,20\n", encoding="utf-8")
    view_b.write_text("id,income\np1,10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must not be present"):
        audit_two_view_linkability(release, view_a, view_b, "id", ["age"], ["income"])


def test_suppression_removes_classes_below_k_without_overwrite(tmp_path: Path) -> None:
    source = _csv(tmp_path / "people.csv")
    output = tmp_path / "suppressed.csv"
    result = suppress_small_classes(source, output, ["zip", "age"], 3)
    assert result["suppressed_records"] == 4
    assert output.read_text() == "zip,age,condition\n"
    with pytest.raises(FileExistsError):
        suppress_small_classes(source, output, ["zip", "age"], 3)


def test_pycanon_utility_metrics_account_for_suppression(tmp_path: Path) -> None:
    raw = tmp_path / "raw.csv"
    anonymized = tmp_path / "anonymized.csv"
    raw.write_text("group,condition\na,A\na,B\nb,A\nc,B\n", encoding="utf-8")
    anonymized.write_text("group,condition\na,A\na,B\n", encoding="utf-8")

    result = audit_csv(anonymized, ["group"], "condition", raw)

    assert result["average_equivalence_class_size"] == 1.0
    assert result["suppressed_records"] == 2
    assert result["discernibility_metric"] == 12  # 2^2 + 2 suppressed * 4 raw
    assert result["classification_metric"] == 0.75  # two suppressed + one minority
    assert result["quasi_identifier_statistics"]["group"] == {
        "distinct_values": 1,
        "minimum_frequency": 2,
        "maximum_frequency": 2,
        "numeric": False,
    }
    assert "A" not in str(result) and "B" not in str(result)


def test_audit_fails_closed_for_missing_declared_column(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing declared"):
        audit_csv(_csv(tmp_path / "people.csv"), ["missing"], "condition")


def test_numeric_emd_t_closeness_is_recomputed(tmp_path: Path) -> None:
    path = tmp_path / "numeric.csv"
    path.write_text("group,income\na,0\na,0\nb,10\nb,10\n", encoding="utf-8")
    result = audit_csv(path, ["group"], "income")
    assert result["numeric_emd_t_closeness"] == 0.5


def test_advanced_transform_enforces_all_declared_bounds(tmp_path: Path) -> None:
    source = tmp_path / "advanced-source.csv"
    source.write_text(
        "group,condition\na,A\na,B\nb,A\nb,B\n", encoding="utf-8"
    )
    output = tmp_path / "advanced-output.csv"
    result = enforce_advanced_privacy_transform(
        source,
        output,
        ["group"],
        "condition",
        {"group": {"a": ["*"], "b": ["*"]}},
        minimum_k=2,
        maximum_alpha=0.5,
        recursive_l=2,
        maximum_recursive_c=1.0,
        maximum_beta=0.0,
        maximum_t=0.0,
    )
    assert result["schema"] == "advanced_privacy_transform.v1"
    assert result["transformation"]["privacy_recomputed"]["k_anonymity"] == 2
    assert result["raw_values_persisted_in_receipt"] is False


def test_advanced_transform_enforces_entropy_and_delta_disclosure(tmp_path: Path) -> None:
    source = tmp_path / "entropy-source.csv"
    source.write_text("group,condition\na,A\na,B\nb,A\nb,B\n", encoding="utf-8")
    output = tmp_path / "entropy-output.csv"
    result = enforce_advanced_privacy_transform(
        source,
        output,
        ["group"],
        "condition",
        {"group": {"a": ["*"], "b": ["*"]}},
        minimum_k=2,
        maximum_alpha=0.5,
        recursive_l=2,
        maximum_recursive_c=1.0,
        maximum_beta=0.0,
        maximum_t=0.0,
        minimum_entropy_l=2.0,
        maximum_delta_disclosure=0.0,
    )
    assert result["bounds"]["minimum_entropy_l"] == 2.0
    assert result["bounds"]["maximum_delta_disclosure"] == 0.0

    rejected = tmp_path / "entropy-rejected.csv"
    with pytest.raises(ValueError, match="entropy_l_diversity"):
        enforce_advanced_privacy_transform(
            source,
            rejected,
            ["group"],
            "condition",
            {"group": {"a": ["*"], "b": ["*"]}},
            minimum_k=2,
            maximum_alpha=1.0,
            recursive_l=2,
            maximum_recursive_c=1.0,
            maximum_beta=1.0,
            maximum_t=1.0,
            minimum_entropy_l=3.0,
        )
    assert not rejected.exists()


def test_advanced_transform_enforces_numeric_emd_and_deletes_output(tmp_path: Path) -> None:
    source = tmp_path / "numeric-advanced.csv"
    source.write_text(
        "group,income\na,0\na,0\na,10\nb,0\nb,10\nb,10\n", encoding="utf-8"
    )
    output = tmp_path / "numeric-must-not-publish.csv"
    with pytest.raises(ValueError, match="numeric_emd_t_closeness"):
        enforce_advanced_privacy_transform(
            source,
            output,
            ["group"],
            "income",
            {"group": {"a": ["*"], "b": ["*"]}},
            minimum_k=3,
            maximum_alpha=1.0,
            recursive_l=2,
            maximum_recursive_c=2.0,
            maximum_beta=1.0,
            maximum_t=1.0,
            maximum_numeric_emd_t=0.1,
        )
    assert not output.exists()


def test_advanced_transform_deletes_output_when_bounds_fail(tmp_path: Path) -> None:
    source = _csv(tmp_path / "advanced-fail.csv")
    output = tmp_path / "must-not-publish.csv"
    with pytest.raises(ValueError, match="advanced privacy bounds unsatisfied"):
        enforce_advanced_privacy_transform(
            source,
            output,
            ["zip", "age"],
            "condition",
            {
                "zip": {"10001": ["*"], "20002": ["*"]},
                "age": {"30": ["*"], "40": ["*"]},
            },
            minimum_k=2,
            maximum_alpha=0.4,
            recursive_l=2,
            maximum_recursive_c=1.0,
            maximum_beta=0.0,
            maximum_t=0.0,
        )
    assert not output.exists()


def test_hierarchy_generalization_selects_minimum_loss_and_recomputes(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        "zip,age,condition\n10001,30,A\n10002,31,B\n20001,40,A\n20002,41,B\n",
        encoding="utf-8",
    )
    output = tmp_path / "generalized.csv"
    result = generalize_with_hierarchies(
        source,
        output,
        ["zip", "age"],
        "condition",
        {
            "zip": {
                "10001": ["1000*", "*****"],
                "10002": ["1000*", "*****"],
                "20001": ["2000*", "*****"],
                "20002": ["2000*", "*****"],
            },
            "age": {
                "30": ["30-39", "*"],
                "31": ["30-39", "*"],
                "40": ["40-49", "*"],
                "41": ["40-49", "*"],
            },
        },
        minimum_k=2,
    )
    assert result["selected_levels"] == {"zip": 1, "age": 1}
    assert result["suppressed_records"] == 0
    assert result["privacy_recomputed"]["k_anonymity"] == 2
    assert output.read_text(encoding="utf-8").splitlines()[1].split(",")[:2] == ["1000*", "30-39"]


def test_singling_out_is_aggregate_and_declared_column_only(tmp_path: Path) -> None:
    source = _csv(tmp_path / "source.csv")
    result = audit_singling_out(source, ["zip", "age"])
    assert result["schema"] == "singling_out_risk.v3"
    assert result["records"] == 4
    assert result["predicates_evaluated"] == 6
    assert result["successful_predicates"] == 0
    assert result["singling_out_rate"] == 0.0
    assert result["random_baseline"] == 0.25
    assert result["excess_over_baseline"] == -0.25
    assert result["confidence_interval_95"][0] == 0.0
    assert result["verdict"] == "clear"
    assert result["raw_values_persisted"] is False
    unique_source = tmp_path / "unique.csv"
    unique_source.write_text("zip,age\n10001,30\n10002,31\n", encoding="utf-8")
    exposed = audit_singling_out(unique_source, ["zip", "age"])
    assert exposed["unique_records"] == 2
    assert exposed["predicates_evaluated"] == 6
    assert exposed["successful_predicates"] == 6
    assert exposed["singling_out_rate"] == 1.0
    singles = audit_singling_out(unique_source, ["zip", "age"], max_predicate_size=1)
    assert singles["predicates_evaluated"] == 4
    assert singles["successful_predicates"] == 4
    assert exposed["verdict"] == "singling_out_risk"
    assert exposed["raw_values_persisted"] is False
    controlled = audit_singling_out(unique_source, ["zip", "age"], control=source)
    assert controlled["control_singling_out_rate"] == 0.0
    assert controlled["control_adjusted_excess"] == 1.0
    assert controlled["risk_threshold_kind"] == "control_data"
    bad_control = tmp_path / "bad.csv"
    bad_control.write_text("zip\n10001\n", encoding="utf-8")
    with pytest.raises(ValueError, match="control missing declared columns"):
        audit_singling_out(unique_source, ["zip", "age"], control=bad_control)
    with pytest.raises(ValueError, match="missing declared columns"):
        audit_singling_out(source, ["unknown"])


def test_microaggregation_and_coding_recomputes_k_and_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "source.csv"
    source.write_text(
        "age,condition\n10,A\n20,B\n90,A\n100,B\n", encoding="utf-8"
    )
    output = tmp_path / "release.csv"
    result = microaggregate_and_code(
        source, output, ["age"], "condition", ["age"], 2, {"age": (15, 95)}
    )
    assert result["schema"] == "microaggregation_and_coding.v1"
    assert result["privacy_recomputed"]["k_anonymity"] == 2
    assert result["raw_values_persisted_in_receipt"] is False
    assert output.read_text().splitlines()[1:] == ["17.5,A", "17.5,B", "92.5,A", "92.5,B"]
    with pytest.raises(FileExistsError):
        microaggregate_and_code(
            source, output, ["age"], "condition", ["age"], 2, {"age": (15, 95)}
        )

    unsafe = tmp_path / "unsafe.csv"
    source.write_text("age,city,condition\n10,X,A\n20,Y,B\n", encoding="utf-8")
    with pytest.raises(ValueError, match="post-transform k-anonymity"):
        microaggregate_and_code(
            source,
            unsafe,
            ["age", "city"],
            "condition",
            ["age"],
            2,
            {"age": (None, None)},
        )
    assert not unsafe.exists()


def test_hierarchy_generalization_fails_closed_on_incomplete_hierarchy(tmp_path: Path) -> None:
    source = _csv(tmp_path / "source.csv")
    with pytest.raises(ValueError, match="does not cover"):
        generalize_with_hierarchies(
            source,
            tmp_path / "out.csv",
            ["zip"],
            "condition",
            {"zip": {"10001": ["1000*"]}},
            minimum_k=2,
        )
