using BarberX.Shared.Services;
using FluentAssertions;
using Xunit;

namespace BarberX.Mobile.Tests.Services;

public class ApiClientTests
{
    [Fact]
    public void ApiClient_ShouldImplementIApiClient()
    {
        // Assert
        typeof(IApiClient).IsInterface.Should().BeTrue();
        typeof(IApiClient).GetMethods().Should().NotBeEmpty();
    }

    [Fact]
    public void IApiClient_ShouldHaveAuthenticationMethods()
    {
        // Assert
        var methods = typeof(IApiClient).GetMethods();
        methods.Should().Contain(m => m.Name == "LoginAsync");
        methods.Should().Contain(m => m.Name == "RegisterAsync");
        methods.Should().Contain(m => m.Name == "LogoutAsync");
        methods.Should().Contain(m => m.Name == "GetProfileAsync");
    }

    [Fact]
    public void IApiClient_ShouldHaveAnalysisMethods()
    {
        // Assert
        var methods = typeof(IApiClient).GetMethods();
        methods.Should().Contain(m => m.Name == "UploadVideoAsync");
        methods.Should().Contain(m => m.Name == "GetAnalysisStatusAsync");
        methods.Should().Contain(m => m.Name == "GetAnalysisResultsAsync");
        methods.Should().Contain(m => m.Name == "GetUserAnalysesAsync");
    }

    [Fact]
    public void IApiClient_ShouldHavePdfMethods()
    {
        // Assert
        var methods = typeof(IApiClient).GetMethods();
        methods.Should().Contain(m => m.Name == "UploadPdfAsync");
        methods.Should().Contain(m => m.Name == "GetUserPdfsAsync");
        methods.Should().Contain(m => m.Name == "AnalyzePdfAsync");
    }

    [Fact]
    public void IApiClient_ShouldHaveSubscriptionMethods()
    {
        // Assert
        var methods = typeof(IApiClient).GetMethods();
        methods.Should().Contain(m => m.Name == "GetUsageStatsAsync");
        methods.Should().Contain(m => m.Name == "GetSubscriptionInfoAsync");
        methods.Should().Contain(m => m.Name == "UpgradeSubscriptionAsync");
    }
}
