"""Schema definitions for configs, manifests, labels, features, and run status."""

from text_factor_lab.schemas.audit import (
    AuditCheckRecord,
    AuditReportRecord,
    CoverageFailureRecord,
)
from text_factor_lab.schemas.config import ExperimentConfig, load_experiment_config
from text_factor_lab.schemas.document_manifest import DocumentManifestRecord
from text_factor_lab.schemas.evaluation import (
    EvaluationMetricRecord,
    FactorPanelRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
    PortfolioReturnRecord,
    PortfolioWeightRecord,
)
from text_factor_lab.schemas.features import FeatureManifestRecord, FeatureRecord
from text_factor_lab.schemas.inference import (
    MultipleTestingFamilyRecord,
    MultipleTestingReportRecord,
    TestedSpecificationRecord,
)
from text_factor_lab.schemas.labels import LabelRecord
from text_factor_lab.schemas.market_data import (
    CRSPDailyReturnRecord,
    CRSPDelistingReturnRecord,
    DataLicenseManifestRecord,
)
from text_factor_lab.schemas.model_manifest import ModelManifestRecord, TuningLogRecord
from text_factor_lab.schemas.parsed_sections import ParsedSectionRecord, ParsingQualityReport
from text_factor_lab.schemas.predictions import ModelPredictionFailureRecord, PredictionRecord
from text_factor_lab.schemas.run_status import RunStatusRecord
from text_factor_lab.schemas.splits import SplitAssignmentRecord, SplitLeakageRecord
from text_factor_lab.schemas.universe import (
    EntityLinkHistoryRecord,
    SecurityMasterRecord,
    UniverseMembershipRecord,
    UniverseQualityReport,
    UniverseRecord,
)

__all__ = [
    "DocumentManifestRecord",
    "ExperimentConfig",
    "AuditCheckRecord",
    "AuditReportRecord",
    "CRSPDailyReturnRecord",
    "CRSPDelistingReturnRecord",
    "DataLicenseManifestRecord",
    "CoverageFailureRecord",
    "EvaluationMetricRecord",
    "EntityLinkHistoryRecord",
    "FactorPanelRecord",
    "FeatureManifestRecord",
    "FeatureRecord",
    "LabelRecord",
    "ModelManifestRecord",
    "MultipleTestingFamilyRecord",
    "MultipleTestingReportRecord",
    "ParsedSectionRecord",
    "ParsingQualityReport",
    "PredictionRecord",
    "ModelPredictionFailureRecord",
    "PortfolioBacktestRecord",
    "PortfolioMetricRecord",
    "PortfolioReturnRecord",
    "PortfolioWeightRecord",
    "RunStatusRecord",
    "SecurityMasterRecord",
    "SplitAssignmentRecord",
    "SplitLeakageRecord",
    "TestedSpecificationRecord",
    "TuningLogRecord",
    "UniverseMembershipRecord",
    "UniverseQualityReport",
    "UniverseRecord",
    "load_experiment_config",
]
