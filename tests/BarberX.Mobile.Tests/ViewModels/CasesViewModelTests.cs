using BarberX.Mobile.ViewModels;
using FluentAssertions;
using Xunit;

namespace BarberX.Mobile.Tests.ViewModels;

public class CasesViewModelTests
{
    private readonly CasesViewModel _viewModel;

    public CasesViewModelTests()
    {
        _viewModel = new CasesViewModel();
    }

    [Fact]
    public void Constructor_ShouldInitializeWithDefaultValues()
    {
        // Assert
        _viewModel.Title.Should().Be("Cases");
        _viewModel.Cases.Should().BeEmpty();
        _viewModel.SearchText.Should().BeEmpty();
        _viewModel.SelectedCase.Should().BeNull();
    }

    [Fact]
    public async Task LoadCasesAsync_ShouldPopulateCasesList()
    {
        // Act
        await _viewModel.LoadCasesAsync();

        // Assert
        _viewModel.Cases.Should().NotBeEmpty();
        _viewModel.Cases.Should().HaveCountGreaterThan(0);
    }

    [Fact]
    public async Task LoadCasesAsync_WhenAlreadyBusy_ShouldNotExecute()
    {
        // Arrange
        _viewModel.IsBusy = true;
        var initialCount = _viewModel.Cases.Count;

        // Act
        await _viewModel.LoadCasesAsync();

        // Assert
        _viewModel.Cases.Count.Should().Be(initialCount);
    }

    [Fact]
    public void SearchCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.SearchCommand.Should().NotBeNull();
    }

    [Fact]
    public void CreateCaseCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.CreateCaseCommand.Should().NotBeNull();
    }

    [Fact]
    public void CaseSelectedCommand_ShouldBeAvailable()
    {
        // Assert
        _viewModel.CaseSelectedCommand.Should().NotBeNull();
    }
}
