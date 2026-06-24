from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, constr


class WorkloadTestScopeChangedWorkloadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_asset_id: constr(min_length=1)


class WorkloadTestScopeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_workloads: list[WorkloadTestScopeChangedWorkloadRequest] = Field(default_factory=list)


class WorkloadTestScopeChangedWorkloadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_asset_id: constr(min_length=1)
    micro_ag_id: constr(min_length=1)


class WorkloadTestScopeEndpointWorkload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_asset_id: constr(min_length=1)
    micro_ag_id: constr(min_length=1)


class WorkloadTestScopeAffectedRelationship(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_workload: WorkloadTestScopeEndpointWorkload
    destination_workload: WorkloadTestScopeEndpointWorkload


class WorkloadTestScopeUnknownWorkload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_asset_id: constr(min_length=1)


class WorkloadTestScopeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_affected_workload_relationships: int = Field(ge=0)
    total_affected_workloads: int = Field(ge=0)
    total_affected_micro_ags: int = Field(ge=0)
    total_unknown_workloads: int = Field(ge=0)


class WorkloadTestScopeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timestamp: str
    environment: constr(min_length=1)
    changed_workloads: list[WorkloadTestScopeChangedWorkloadResponse]
    affected_workload_relationships: list[WorkloadTestScopeAffectedRelationship]
    unknown_workloads: list[WorkloadTestScopeUnknownWorkload]
    summary: WorkloadTestScopeSummary
