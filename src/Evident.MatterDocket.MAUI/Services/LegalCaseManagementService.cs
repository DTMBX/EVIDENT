using Evident.MatterDocket.MAUI.Models;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace Evident.MatterDocket.MAUI.Services
{
    /// <summary>
    /// Service for managing legal cases with full e-discovery support
    /// Handles case lifecycle, evidence organization, and legal compliance
    /// </summary>
    public interface ILegalCaseManagementService
    {
        Task<ApiResponse<LegalCase>> GetCaseAsync(string caseId);
        Task<ApiResponse<List<LegalCase>>> GetCasesAsync(int page = 1, int pageSize = 20);
        Task<ApiResponse<LegalCase>> CreateCaseAsync(LegalCase caseData);
        Task<ApiResponse<LegalCase>> UpdateCaseAsync(string caseId, LegalCase caseData);
        Task<ApiResponse<bool>> DeleteCaseAsync(string caseId);
        Task<ApiResponse<List<LegalCase>>> SearchCasesAsync(string query);
        Task<ApiResponse<bool>> EnforceLegalHoldAsync(string caseId);
        Task<ApiResponse<bool>> RemoveLegalHoldAsync(string caseId);
        Task<ApiResponse<CaseStatistics>> GetCaseStatisticsAsync(string caseId);
    }

    public class LegalCaseManagementService : ILegalCaseManagementService
    {
        private readonly IApiService _apiService;
        private readonly IAuditLogService _auditLogService;

        public LegalCaseManagementService(IApiService apiService, IAuditLogService auditLogService)
        {
            _apiService = apiService;
            _auditLogService = auditLogService;
        }

        /// <summary>
        /// Retrieve a specific legal case with all related data
        /// </summary>
        public async Task<ApiResponse<LegalCase>> GetCaseAsync(string caseId)
        {
            try
            {
                var response = await _apiService.GetAsync<LegalCase>($"/api/v1/cases/{caseId}");
                
                if (response.Success)
                {
                    // Log access to audit trail
                    await _auditLogService.LogAccessAsync(caseId, "CaseViewed", "Case details accessed");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                return new ApiResponse<LegalCase>
                {
                    Success = false,
                    Error = $"Failed to retrieve case: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// List all cases accessible to current user with pagination
        /// </summary>
        public async Task<ApiResponse<List<LegalCase>>> GetCasesAsync(int page = 1, int pageSize = 20)
        {
            try
            {
                return await _apiService.GetAsync<List<LegalCase>>($"/api/v1/cases?page={page}&pageSize={pageSize}");
            }
            catch (Exception ex)
            {
                return new ApiResponse<List<LegalCase>>
                {
                    Success = false,
                    Error = $"Failed to retrieve cases: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Create a new legal case with metadata
        /// </summary>
        public async Task<ApiResponse<LegalCase>> CreateCaseAsync(LegalCase caseData)
        {
            try
            {
                caseData.CreatedAt = DateTime.UtcNow;
                caseData.UpdatedAt = DateTime.UtcNow;
                
                var response = await _apiService.PostAsync<LegalCase>("/api/v1/cases", caseData);
                
                if (response.Success)
                {
                    await _auditLogService.LogActionAsync(caseData.Id, "CaseCreated", 
                        $"New case created: {caseData.CaseName}");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                return new ApiResponse<LegalCase>
                {
                    Success = false,
                    Error = $"Failed to create case: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Update existing case information
        /// </summary>
        public async Task<ApiResponse<LegalCase>> UpdateCaseAsync(string caseId, LegalCase caseData)
        {
            try
            {
                caseData.UpdatedAt = DateTime.UtcNow;
                
                var response = await _apiService.PutAsync<LegalCase>($"/api/v1/cases/{caseId}", caseData);
                
                if (response.Success)
                {
                    await _auditLogService.LogActionAsync(caseId, "CaseUpdated", 
                        $"Case information updated");
                }
                
                return response;
            }
            catch (Exception ex)
            {
                return new ApiResponse<LegalCase>
                {
                    Success = false,
                    Error = $"Failed to update case: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Delete a case (soft delete - archives case)
        /// </summary>
        public async Task<ApiResponse<bool>> DeleteCaseAsync(string caseId)
        {
            try
            {
                var response = await _apiService.DeleteAsync($"/api/v1/cases/{caseId}");
                
                if (response.Success)
                {
                    await _auditLogService.LogActionAsync(caseId, "CaseDeleted", 
                        $"Case archived/deleted");
                }
                
                return new ApiResponse<bool> { Success = response.Success, Data = true };
            }
            catch (Exception ex)
            {
                return new ApiResponse<bool>
                {
                    Success = false,
                    Error = $"Failed to delete case: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Search cases by name, number, or jurisdiction
        /// </summary>
        public async Task<ApiResponse<List<LegalCase>>> SearchCasesAsync(string query)
        {
            try
            {
                return await _apiService.GetAsync<List<LegalCase>>($"/api/v1/cases/search?q={Uri.EscapeDataString(query)}");
            }
            catch (Exception ex)
            {
                return new ApiResponse<List<LegalCase>>
                {
                    Success = false,
                    Error = $"Failed to search cases: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Activate legal hold on case - prevents evidence deletion/modification
        /// </summary>
        public async Task<ApiResponse<bool>> EnforceLegalHoldAsync(string caseId)
        {
            try
            {
                var response = await _apiService.PostAsync<object>($"/api/v1/cases/{caseId}/legal-hold/activate", null);
                
                if (response.Success)
                {
                    await _auditLogService.LogActionAsync(caseId, "LegalHoldActivated", 
                        $"Legal hold activated on case");
                }
                
                return new ApiResponse<bool> { Success = response.Success, Data = true };
            }
            catch (Exception ex)
            {
                return new ApiResponse<bool>
                {
                    Success = false,
                    Error = $"Failed to activate legal hold: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Remove legal hold restrictions from case
        /// </summary>
        public async Task<ApiResponse<bool>> RemoveLegalHoldAsync(string caseId)
        {
            try
            {
                var response = await _apiService.PostAsync<object>($"/api/v1/cases/{caseId}/legal-hold/deactivate", null);
                
                if (response.Success)
                {
                    await _auditLogService.LogActionAsync(caseId, "LegalHoldDeactivated", 
                        $"Legal hold removed from case");
                }
                
                return new ApiResponse<bool> { Success = response.Success, Data = true };
            }
            catch (Exception ex)
            {
                return new ApiResponse<bool>
                {
                    Success = false,
                    Error = $"Failed to remove legal hold: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Get case statistics for reporting
        /// </summary>
        public async Task<ApiResponse<CaseStatistics>> GetCaseStatisticsAsync(string caseId)
        {
            try
            {
                return await _apiService.GetAsync<CaseStatistics>($"/api/v1/cases/{caseId}/statistics");
            }
            catch (Exception ex)
            {
                return new ApiResponse<CaseStatistics>
                {
                    Success = false,
                    Error = $"Failed to get case statistics: {ex.Message}"
                };
            }
        }
    }

    /// <summary>
    /// Case statistics for reporting and compliance monitoring
    /// </summary>
    public class CaseStatistics
    {
        public string CaseId { get; set; } = string.Empty;
        public int TotalEvidenceItems { get; set; }
        public int TotalDocuments { get; set; }
        public long TotalStorageBytes { get; set; }
        public int TotalParties { get; set; }
        public int PrivilegedDocuments { get; set; }
        public int RedactedDocuments { get; set; }
        public int AuditLogEntries { get; set; }
        public DateTime CaseCreatedDate { get; set; }
        public DateTime LastModifiedDate { get; set; }
    }
}
