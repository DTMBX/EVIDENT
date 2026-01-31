using BarberX.Mobile.ViewModels;
using BarberX.Shared.Services;
using FluentAssertions;
using Moq;
using Xunit;

namespace BarberX.Mobile.Tests.ViewModels;

public class ProfileViewModelTests
{
    private readonly Mock<IApiClient> _mockApiClient;
    private readonly ProfileViewModel _viewModel;

    public ProfileViewModelTests()
    {
        _mockApiClient = new Mock<IApiClient>();
        _viewModel = new ProfileViewModel(_mockApiClient.Object);
    }

    [Fact]
    public void Constructor_ShouldInitializeWithDefaultValues()
    {
        // Assert
        _viewModel.Title.Should().Be("Profile");
        _viewModel.FullName.Should().BeEmpty();
        _viewModel.Email.Should().BeEmpty();
        _viewModel.TierLevel.Should().Be("Free");
        _viewModel.IsFreeTier.Should().BeTrue();
    }

    [Fact]
    public async Task LoadProfileAsync_ShouldLoadUserData()
    {
        // Arrange
        var mockProfile = new UserProfile
        {
            FullName = "Jane Smith",
            Email = "jane@example.com",
            Tier = "PREMIUM",
            Organization = "Smith Law Firm",
            CreatedAt = DateTime.Now.AddYears(-1)
        };
        _mockApiClient.Setup(x => x.GetProfileAsync())
            .ReturnsAsync(mockProfile);

        var mockUsage = new UsageStats
        {
            BwcVideosProcessed = 10,
            PdfDocumentsProcessed = 25,
            StorageUsedMb = 512.5
        };
        _mockApiClient.Setup(x => x.GetUsageStatsAsync())
            .ReturnsAsync(mockUsage);

        // Act
        await _viewModel.LoadProfileAsync();

        // Assert
        _viewModel.FullName.Should().Be("Jane Smith");
        _viewModel.Email.Should().Be("jane@example.com");
        _viewModel.TierLevel.Should().Be("PREMIUM");
        _viewModel.Organization.Should().Be("Smith Law Firm");
        _viewModel.IsFreeTier.Should().BeFalse();
        _viewModel.VideosAnalyzed.Should().Be(10);
        _viewModel.DocumentsProcessed.Should().Be(25);
        _viewModel.StorageUsed.Should().Be("512.50 MB");
    }

    [Fact]
    public async Task LoadProfileAsync_WhenAlreadyBusy_ShouldNotExecute()
    {
        // Arrange
        _viewModel.IsBusy = true;

        // Act
        await _viewModel.LoadProfileAsync();

        // Assert
        _mockApiClient.Verify(x => x.GetProfileAsync(), Times.Never);
    }

    [Fact]
    public void EditProfileCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.EditProfileCommand.Should().NotBeNull();
    }

    [Fact]
    public void ChangePasswordCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.ChangePasswordCommand.Should().NotBeNull();
    }

    [Fact]
    public void UpgradeCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.UpgradeCommand.Should().NotBeNull();
    }
}
