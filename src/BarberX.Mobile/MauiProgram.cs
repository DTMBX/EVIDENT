using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using BarberX.Mobile.Services;
using BarberX.Mobile.ViewModels;
using BarberX.Mobile.Views;
using BarberX.Shared.Services;
using System.Reflection;

namespace BarberX.Mobile;

public static class MauiProgram
{
	public static MauiApp CreateMauiApp()
	{
		var builder = MauiApp.CreateBuilder();
		builder
			.UseMauiApp<App>()
			.ConfigureFonts(fonts =>
			{
				fonts.AddFont("OpenSans-Regular.ttf", "OpenSansRegular");
				fonts.AddFont("OpenSans-Semibold.ttf", "OpenSansSemibold");
			});

		// Load configuration from appsettings.json
		var assembly = Assembly.GetExecutingAssembly();
		using var stream = assembly.GetManifestResourceStream("BarberX.Mobile.appsettings.json");
		if (stream != null)
		{
			var config = new ConfigurationBuilder()
				.AddJsonStream(stream)
				.Build();
			builder.Configuration.AddConfiguration(config);
		}

#if DEBUG
		builder.Logging.AddDebug();
		builder.Logging.SetMinimumLevel(LogLevel.Debug);
#else
		builder.Logging.SetMinimumLevel(LogLevel.Warning);
#endif

		// Get API endpoint from configuration based on environment
		var apiEndpoint = GetApiEndpoint(builder.Configuration);
		var apiTimeout = builder.Configuration.GetValue<int>("Timeouts:ApiTimeoutMinutes", 5);

		// Register HttpClient with base address
		builder.Services.AddHttpClient<IApiClient, ApiClient>(client =>
		{
			client.BaseAddress = new Uri(apiEndpoint);
			client.Timeout = TimeSpan.FromMinutes(apiTimeout);
			client.DefaultRequestHeaders.Add("User-Agent", "BarberX-Mobile/1.0");
			client.DefaultRequestHeaders.Add("X-App-Platform", DeviceInfo.Platform.ToString());
			client.DefaultRequestHeaders.Add("X-App-Version", AppInfo.VersionString);
		});

		// Register services
		builder.Services.AddSingleton<AuthService>();
		builder.Services.AddSingleton<ITierService, TierService>();
		
		// Register ViewModels
		builder.Services.AddTransient<LoginViewModel>();
		builder.Services.AddTransient<DashboardViewModel>();
		builder.Services.AddTransient<CasesViewModel>();
		builder.Services.AddTransient<AnalysisListViewModel>();
		builder.Services.AddTransient<UploadViewModel>();
		builder.Services.AddTransient<AnalysisDetailViewModel>();
		builder.Services.AddTransient<ProfileViewModel>();
		builder.Services.AddTransient<SettingsViewModel>();
		
		// Register Views
		builder.Services.AddTransient<LoginPage>();
		builder.Services.AddTransient<DashboardPage>();
		builder.Services.AddTransient<CasesPage>();
		builder.Services.AddTransient<AnalysisListPage>();
		builder.Services.AddTransient<UploadPage>();
		builder.Services.AddTransient<AnalysisDetailPage>();
		builder.Services.AddTransient<ProfilePage>();
		builder.Services.AddTransient<SettingsPage>();
		builder.Services.AddTransient<CaseDetailPage>();
		builder.Services.AddTransient<DocumentViewerPage>();
		builder.Services.AddTransient<VideoAnalysisPage>();
		builder.Services.AddTransient<TranscriptViewerPage>();
		builder.Services.AddTransient<LegalLibraryPage>();
		builder.Services.AddTransient<DocumentsPage>();

		return builder.Build();
	}

	private static string GetApiEndpoint(IConfiguration configuration)
	{
		// Check for environment variable override
		var envEndpoint = Environment.GetEnvironmentVariable("BARBERX_API_ENDPOINT");
		if (!string.IsNullOrEmpty(envEndpoint))
		{
			return envEndpoint;
		}

		// Determine environment
		var environment = GetEnvironment();
		
		return environment switch
		{
			"Development" => configuration["ApiEndpoints:Development"] ?? "http://localhost:5000",
			"Staging" => configuration["ApiEndpoints:Staging"] ?? "https://staging-api.barberx.info",
			"Production" => configuration["ApiEndpoints:Production"] ?? "https://api.barberx.info",
			_ => configuration["ApiEndpoints:Production"] ?? "https://api.barberx.info"
		};
	}

	private static string GetEnvironment()
	{
#if DEBUG
		return "Development";
#elif STAGING
		return "Staging";
#else
		return "Production";
#endif
	}
}
