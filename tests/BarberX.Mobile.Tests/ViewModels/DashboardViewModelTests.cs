using BarberX.Mobile.ViewModels;
using BarberX.Shared.Services;
using FluentAssertions;
using Moq;
using Xunit;

namespace BarberX.Mobile.Tests.ViewModels;

public class DashboardViewModelTests
{
    private readonly Mock<IApiClient> _mockApiClient;
    private readonly DashboardViewModel _viewModel;

    public DashboardViewModelTests()
    {
        _mockApiClient = new Mock<IApiClient>();
        _viewModel = new DashboardViewModel(_mockApiClient.Object);
    }

    [Fact]
    public void Constructor_ShouldInitializeWithDefaultValues()
    {
        // Assert
        _viewModel.Title.Should().Be("Dashboard");
        _viewModel.UserName.Should().Be("User");
        _viewModel.TotalCases.Should().Be(0);
        _viewModel.TotalAnalyses.Should().Be(0);
        _viewModel.IsFreeTier.Should().BeTrue();
    }

    [Fact]
    public async Task InitializeAsync_ShouldLoadUserProfile()
    {
        // Arrange
        var mockProfile = new UserProfile
        {
            FullName = "John Doe",
            Tier = "FREE"
        };
        _mockApiClient.Setup(x => x.GetProfileAsync())
            .ReturnsAsync(mockProfile);

        var mockUsage = new UsageStats
        {
            BwcVideosProcessed = 3,
            PdfDocumentsProcessed = 5
        };
        _mockApiClient.Setup(x => x.GetUsageStatsAsync())
            .ReturnsAsync(mockUsage);

        // Act
        await _viewModel.InitializeAsync();

        // Assert
        _viewModel.UserName.Should().Be("John Doe");
        _viewModel.IsFreeTier.Should().BeTrue();
        _viewModel.TotalAnalyses.Should().Be(3);
        _viewModel.TotalDocuments.Should().Be(5);
    }

    [Fact]
    public async Task InitializeAsync_ShouldCalculateUsagePercentage()
    {
        // Arrange
        var mockProfile = new UserProfile { Tier = "FREE" };
        _mockApiClient.Setup(x => x.GetProfileAsync())
            .ReturnsAsync(mockProfile);

        var mockUsage = new UsageStats
        {
            BwcVideosProcessed = 2,
            MonthlyLimits = new Dictionary<string, int> { { "analyses", 5 } }
        };
        _mockApiClient.Setup(x => x.GetUsageStatsAsync())
            .ReturnsAsync(mockUsage);

        // Act
        await _viewModel.InitializeAsync();

        // Assert
        _viewModel.UsagePercentage.Should().Be(0.4); // 2/5 = 0.4
        _viewModel.UsageText.Should().Be("2 of 5 analyses used");
    }

    [Fact]
    public async Task InitializeAsync_WhenAlreadyBusy_ShouldNotExecute()
    {
        // Arrange
        _viewModel.IsBusy = true;

        // Act
        await _viewModel.InitializeAsync();

        // Assert
        _mockApiClient.Verify(x => x.GetProfileAsync(), Times.Never);
    }

    [Fact]
    public async Task NavigateToUploadCommand_ShouldNavigateToUploadPage()
    {
        // Note: Navigation testing requires Shell mock or integration test
        // This is a placeholder for the command structure
        _viewModel.NavigateToUploadCommand.Should().NotBeNull();
    }
}
