/**
 * VIDEO BATCH PROCESSOR - Windows Desktop UI (WPF/C#)
 * Native Windows application for video processing management
 * 
 * Architecture: MVVM pattern, async/await for long-running operations
 * Platform: .NET 8.0, WPF
 */

using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Collections.Generic;
using System.Linq;

namespace Evident.VideoProcessor.Desktop
{
    // ======================== DESIGN TOKENS ========================
    public static class DesignTokens
    {
        public static readonly Color PrimaryColor = Color.FromRgb(0x0b, 0x73, 0xd2);
        public static readonly Color AccentColor = Color.FromRgb(0xe0, 0x7a, 0x5f);
        public static readonly Color NeutralColor = Color.FromRgb(0xf6, 0xf7, 0xf9);
        public static readonly Color DarkColor = Color.FromRgb(0x1a, 0x1a, 0x1a);
        public static readonly Color SuccessColor = Color.FromRgb(0x4c, 0xaf, 0x50);
        public static readonly Color WarningColor = Color.FromRgb(0xff, 0x98, 0x00);
        public static readonly Color ErrorColor = Color.FromRgb(0xf4, 0x43, 0x36);

        public const double SpacingXS = 4.0;
        public const double SpacingSM = 8.0;
        public const double SpacingMD = 16.0;
        public const double SpacingLG = 24.0;
        public const double SpacingXL = 32.0;

        public const double FontSizeBody = 14.0;
        public const double FontSizeHeading = 20.0;
        public const double FontSizeLarge = 24.0;
    }

    // ======================== MVVM BASE CLASSES ========================

    public class RelayCommand : ICommand
    {
        private Action<object> execute;
        private Predicate<object> canExecute;

        public event EventHandler CanExecuteChanged
        {
            add { CommandManager.RequerySuggested += value; }
            remove { CommandManager.RequerySuggested -= value; }
        }

        public RelayCommand(Action<object> execute, Predicate<object> canExecute = null)
        {
            this.execute = execute;
            this.canExecute = canExecute;
        }

        public bool CanExecute(object parameter) => canExecute == null || canExecute(parameter);
        public void Execute(object parameter) => execute(parameter);
    }

    public class ViewModelBase : INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;

        protected void OnPropertyChanged([CallerMemberName] string name = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
        }

        protected bool SetProperty<T>(ref T storage, T value, [CallerMemberName] string propertyName = null)
        {
            if (Equals(storage, value)) return false;
            storage = value;
            OnPropertyChanged(propertyName);
            return true;
        }
    }

    // ======================== MODEL CLASSES ========================

    public class VideoFile : ViewModelBase
    {
        private string id;
        private string name;
        private long sizeBytes;
        private VideoProcessingStatus status;
        private double progress;

        public string Id { get => id; set => SetProperty(ref id, value); }
        public string Name { get => name; set => SetProperty(ref name, value); }
        public long SizeBytes { get => sizeBytes; set => SetProperty(ref sizeBytes, value); }
        public VideoProcessingStatus Status { get => status; set => SetProperty(ref status, value); }
        public double Progress { get => progress; set => SetProperty(ref progress, value); }

        public string SizeDisplay => FormatBytes(SizeBytes);
        public string StatusDisplay => Status.GetDescription();

        public static string FormatBytes(long bytes)
        {
            string[] sizes = { "B", "KB", "MB", "GB" };
            double len = bytes;
            int order = 0;

            while (len >= 1024 && order < sizes.Length - 1)
            {
                order++;
                len = len / 1024;
            }

            return $"{len:0.##} {sizes[order]}";
        }
    }

    public enum VideoProcessingStatus
    {
        [Description("Pending")]
        Pending,

        [Description("Uploading")]
        Uploading,

        [Description("Processing")]
        Processing,

        [Description("Transcribing")]
        Transcribing,

        [Description("Synchronizing")]
        Synchronizing,

        [Description("Complete")]
        Complete,

        [Description("Error")]
        Error
    }

    public class BatchUploadModel : ViewModelBase
    {
        private string batchId;
        private string caseId;
        private string quality;
        private bool syncBwc;
        private bool extractTranscription;
        private ObservableCollection<VideoFile> files;
        private double overallProgress;
        private BatchStatus status;
        private DateTime createdAt;

        public string BatchId { get => batchId; set => SetProperty(ref batchId, value); }
        public string CaseId { get => caseId; set => SetProperty(ref caseId, value); }
        public string Quality { get => quality; set => SetProperty(ref quality, value); }
        public bool SyncBwc { get => syncBwc; set => SetProperty(ref syncBwc, value); }
        public bool ExtractTranscription { get => extractTranscription; set => SetProperty(ref extractTranscription, value); }
        public ObservableCollection<VideoFile> Files { get => files; set => SetProperty(ref files, value); }
        public double OverallProgress { get => overallProgress; set => SetProperty(ref overallProgress, value); }
        public BatchStatus Status { get => status; set => SetProperty(ref status, value); }
        public DateTime CreatedAt { get => createdAt; set => SetProperty(ref createdAt, value); }

        public string StatusDisplay => Status.ToString();
        public string FileCount => $"{Files.Count} files";

        public BatchUploadModel()
        {
            Files = new ObservableCollection<VideoFile>();
            CreatedAt = DateTime.Now;
        }
    }

    public enum BatchStatus
    {
        Queued,
        Processing,
        Complete,
        Error,
        Cancelled
    }

    // ======================== VIEW MODELS ========================

    public class FileUploadViewModel : ViewModelBase
    {
        private List<string> selectedFilePaths;
        private string caseId;
        private string quality;
        private bool syncBwc = true;
        private bool extractTranscription = true;
        private bool isLoading;
        private string statusMessage;

        public ICommand SelectFilesCommand { get; }
        public ICommand SubmitUploadCommand { get; }
        public ICommand ClearCommand { get; }

        public List<string> SelectedFilePaths
        {
            get => selectedFilePaths;
            set => SetProperty(ref selectedFilePaths, value);
        }

        public string CaseId { get => caseId; set => SetProperty(ref caseId, value); }
        public string Quality { get => quality; set => SetProperty(ref quality, value); }
        public bool SyncBwc { get => syncBwc; set => SetProperty(ref syncBwc, value); }
        public bool ExtractTranscription { get => extractTranscription; set => SetProperty(ref extractTranscription, value); }
        public bool IsLoading { get => isLoading; set => SetProperty(ref isLoading, value); }
        public string StatusMessage { get => statusMessage; set => SetProperty(ref statusMessage, value); }

        public string FileCountDisplay => SelectedFilePaths?.Count > 0 ? $"{SelectedFilePaths.Count} file(s)" : "No files selected";
        public bool CanSubmit => SelectedFilePaths?.Count > 0 && !string.IsNullOrEmpty(CaseId) && !IsLoading;

        public FileUploadViewModel()
        {
            SelectedFilePaths = new List<string>();
            Quality = "high";
            SelectFilesCommand = new RelayCommand(_ => SelectFiles());
            SubmitUploadCommand = new RelayCommand(_ => SubmitUpload(), _ => CanSubmit);
            ClearCommand = new RelayCommand(_ => Clear());
        }

        private void SelectFiles()
        {
            var dialog = new System.Windows.Forms.OpenFileDialog
            {
                Multiselect = true,
                Filter = "Video Files (*.mp4;*.mov;*.avi;*.mkv)|*.mp4;*.mov;*.avi;*.mkv|All Files (*.*)|*.*"
            };

            if (dialog.ShowDialog() == System.Windows.Forms.DialogResult.OK)
            {
                SelectedFilePaths = new List<string>(dialog.FileNames);
                OnPropertyChanged(nameof(FileCountDisplay));
                OnPropertyChanged(nameof(CanSubmit));
            }
        }

        private async void SubmitUpload()
        {
            IsLoading = true;
            try
            {
                StatusMessage = "Uploading files...";

                // TODO: Send to API
                await Task.Delay(2000); // Simulate upload

                StatusMessage = "✓ Upload submitted successfully";
                Clear();
            }
            catch (Exception ex)
            {
                StatusMessage = $"✗ Error: {ex.Message}";
            }
            finally
            {
                IsLoading = false;
            }
        }

        private void Clear()
        {
            SelectedFilePaths.Clear();
            CaseId = "";
            Quality = "high";
            SyncBwc = true;
            ExtractTranscription = true;
            StatusMessage = "";
            OnPropertyChanged(nameof(FileCountDisplay));
            OnPropertyChanged(nameof(CanSubmit));
        }
    }

    public class BatchProcessingViewModel : ViewModelBase
    {
        private ObservableCollection<BatchUploadModel> batches;
        private BatchUploadModel selectedBatch;
        private double refreshIntervalSeconds = 1.0;

        public ObservableCollection<BatchUploadModel> Batches 
        { 
            get => batches; 
            set => SetProperty(ref batches, value); 
        }

        public BatchUploadModel SelectedBatch 
        { 
            get => selectedBatch; 
            set => SetProperty(ref selectedBatch, value); 
        }

        public ICommand RefreshCommand { get; }
        public ICommand CancelBatchCommand { get; }

        public BatchProcessingViewModel()
        {
            Batches = new ObservableCollection<BatchUploadModel>();
            RefreshCommand = new RelayCommand(_ => Refresh());
            CancelBatchCommand = new RelayCommand(batch => CancelBatch(batch as BatchUploadModel));

            // Simulate some batches for demo
            LoadDemoBatches();
        }

        private void LoadDemoBatches()
        {
            Batches.Add(new BatchUploadModel
            {
                BatchId = "batch_20250131_001",
                CaseId = "case_2026_001",
                Quality = "high",
                Status = BatchStatus.Processing,
                OverallProgress = 65.0,
                Files = new ObservableCollection<VideoFile>
                {
                    new VideoFile { Name = "camera_1.mp4", Status = VideoProcessingStatus.Complete, Progress = 100, SizeBytes = 1024*1024*500 },
                    new VideoFile { Name = "camera_2.mp4", Status = VideoProcessingStatus.Transcribing, Progress = 75, SizeBytes = 1024*1024*480 },
                    new VideoFile { Name = "camera_3.mp4", Status = VideoProcessingStatus.Processing, Progress = 50, SizeBytes = 1024*1024*510 },
                }
            });

            Batches.Add(new BatchUploadModel
            {
                BatchId = "batch_20250130_001",
                CaseId = "case_2026_002",
                Quality = "medium",
                Status = BatchStatus.Complete,
                OverallProgress = 100.0,
                Files = new ObservableCollection<VideoFile>
                {
                    new VideoFile { Name = "footage_a.mov", Status = VideoProcessingStatus.Complete, Progress = 100, SizeBytes = 1024*1024*420 },
                    new VideoFile { Name = "footage_b.mov", Status = VideoProcessingStatus.Complete, Progress = 100, SizeBytes = 1024*1024*450 },
                }
            });
        }

        private void Refresh()
        {
            // TODO: Fetch updates from API
        }

        private void CancelBatch(BatchUploadModel batch)
        {
            if (batch != null)
            {
                batch.Status = BatchStatus.Cancelled;
            }
        }
    }

    // ======================== VIEWS (XAML-BASED) ========================

    public partial class FileUploadUserControl : UserControl
    {
        public FileUploadUserControl()
        {
            InitializeComponent();
            DataContext = new FileUploadViewModel();
        }
    }

    public partial class BatchProgressUserControl : UserControl
    {
        public BatchProgressUserControl()
        {
            InitializeComponent();
            DataContext = new BatchProcessingViewModel();
        }
    }

    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }
    }
}

// ======================== XAML DEFINITIONS (as string definitions) ========================

/*
MAINWINDOW.XAML:

<Window x:Class="Evident.VideoProcessor.Desktop.MainWindow"
        xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="🎥 Evident Video Batch Processor"
        Width="1400"
        Height="900"
        WindowStartupLocation="CenterScreen"
        Background="#f6f7f9">
    <Grid>
        <Grid.ColumnDefinitions>
            <ColumnDefinition Width="600"/>
            <ColumnDefinition Width="*"/>
        </Grid.ColumnDefinitions>

        <!-- Header -->
        <StackPanel Grid.ColumnSpan="2" Orientation="Vertical" Background="#0b73d2" Padding="24">
            <TextBlock Text="🎥 Video Batch Processing" FontSize="24" FontWeight="SemiBold" Foreground="White"/>
            <TextBlock Text="Upload, transcribe, and sync multiple videos in parallel" 
                       FontSize="14" Foreground="White" Margin="0,8,0,0" Opacity="0.9"/>
        </StackPanel>

        <!-- Upload Form -->
        <Border Grid.Row="1" Background="White" Margin="16" Padding="24" CornerRadius="8">
            <local:FileUploadUserControl/>
        </Border>

        <!-- Progress Monitor -->
        <Border Grid.Row="1" Grid.Column="1" Background="White" Margin="16" Padding="24" CornerRadius="8">
            <local:BatchProgressUserControl/>
        </Border>
    </Grid>
</Window>

FILE UPLOAD CONTROL XAML:

<UserControl x:Class="Evident.VideoProcessor.Desktop.FileUploadUserControl"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <StackPanel Orientation="Vertical" Margin="0">
        
        <TextBlock Text="📋 Select Videos" FontSize="20" FontWeight="SemiBold" 
                   Foreground="#0b73d2" Margin="0,0,0,16"/>

        <!-- File Selection -->
        <Border BorderThickness="2" BorderBrush="#0b73d2" Padding="16" 
                CornerRadius="8" Background="#f6f7f9" Margin="0,0,0,16">
            <StackPanel Orientation="Vertical">
                <TextBlock Text="📹" FontSize="32" TextAlignment="Center"/>
                <TextBlock Text="{Binding FileCountDisplay}" FontSize="16" FontWeight="SemiBold" 
                           Foreground="#0b73d2" Margin="0,16,0,0" TextAlignment="Center"/>
                <TextBlock Text="Click button to browse for videos" FontSize="12" 
                           Foreground="#1a1a1a" Margin="0,8,0,0" TextAlignment="Center"/>
                <Button Command="{Binding SelectFilesCommand}" 
                        Content="📂 Browse for Videos" 
                        Padding="16" Margin="0,16,0,0"
                        Background="#0b73d2" Foreground="White" 
                        FontWeight="SemiBold"/>
            </StackPanel>
        </Border>

        <!-- Case ID -->
        <TextBlock Text="📋 Case ID" FontWeight="SemiBold" Margin="0,0,0,8"/>
        <TextBox Text="{Binding CaseId, UpdateSourceTrigger=PropertyChanged}" 
                 Padding="12" Margin="0,0,0,16"
                 PlaceholderText="e.g. case_2026_001"/>

        <!-- Quality Selection -->
        <TextBlock Text="⚙️ Quality Preset" FontWeight="SemiBold" Margin="0,0,0,8"/>
        <ComboBox SelectedItem="{Binding Quality}" Padding="12" Margin="0,0,0,16">
            <ComboBoxItem>ultra_low</ComboBoxItem>
            <ComboBoxItem>low</ComboBoxItem>
            <ComboBoxItem>medium</ComboBoxItem>
            <ComboBoxItem Selected="True">high</ComboBoxItem>
            <ComboBoxItem>ultra_high</ComboBoxItem>
        </ComboBox>

        <!-- Options -->
        <CheckBox IsChecked="{Binding ExtractTranscription}" Margin="0,0,0,8">
            <TextBlock Text="🎤 Extract Transcription (Whisper)"/>
        </CheckBox>
        <CheckBox IsChecked="{Binding SyncBwc}" Margin="0,0,0,16">
            <TextBlock Text="📹 Auto-Sync Multiple Cameras"/>
        </CheckBox>

        <!-- Submit -->
        <Button Command="{Binding SubmitUploadCommand}"
                Content="{Binding SubmitButtonText}"
                Padding="16" Height="40"
                Background="#0b73d2" Foreground="White"
                FontSize="14" FontWeight="SemiBold"
                IsEnabled="{Binding CanSubmit}"/>

        <!-- Status -->
        <TextBlock Text="{Binding StatusMessage}" 
                   Foreground="#0b73d2" Margin="0,16,0,0"
                   TextWrapping="Wrap"/>

    </StackPanel>
</UserControl>

BATCH PROGRESS CONTROL XAML:

<UserControl x:Class="Evident.VideoProcessor.Desktop.BatchProgressUserControl"
             xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
             xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
    <StackPanel Orientation="Vertical">
        
        <TextBlock Text="📊 Processing Status" FontSize="20" FontWeight="SemiBold" 
                   Foreground="#0b73d2" Margin="0,0,0,16"/>

        <!-- Batch List -->
        <DataGrid ItemsSource="{Binding Batches}" SelectedItem="{Binding SelectedBatch}"
                  AutoGenerateColumns="False" CanUserAddRows="False"
                  Margin="0,0,0,16">
            <DataGrid.Columns>
                <DataGridTextColumn Header="Batch ID" Binding="{Binding BatchId}" Width="150"/>
                <DataGridTextColumn Header="Case" Binding="{Binding CaseId}" Width="100"/>
                <DataGridTextColumn Header="Files" Binding="{Binding FileCount}" Width="80"/>
                <DataGridTextColumn Header="Status" Binding="{Binding StatusDisplay}" Width="80"/>
                <DataGridTextColumn Header="Progress" Binding="{Binding OverallProgress, StringFormat='{0:F0}%'}" Width="80"/>
            </DataGrid.Columns>
        </DataGrid>

        <!-- Selected Batch Details -->
        <Expander Header="📋 Batch Details" IsExpanded="True" Margin="0,0,0,16">
            <StackPanel Orientation="Vertical" Padding="16">
                <TextBlock Text="Files:" FontWeight="SemiBold" Margin="0,0,0,8"/>
                <ListBox ItemsSource="{Binding SelectedBatch.Files}" Height="250">
                    <ListBox.ItemTemplate>
                        <DataTemplate>
                            <Border Padding="8" BorderThickness="0,0,0,1" BorderBrush="#f6f7f9">
                                <StackPanel Orientation="Vertical">
                                    <TextBlock Text="{Binding Name}" FontWeight="SemiBold"/>
                                    <ProgressBar Value="{Binding Progress}" Height="12" 
                                                 Foreground="#0b73d2" Margin="0,4,0,0"/>
                                    <TextBlock Text="{Binding StatusDisplay}" 
                                               Foreground="#0b73d2" FontSize="12" Margin="0,2,0,0"/>
                                </StackPanel>
                            </Border>
                        </DataTemplate>
                    </ListBox.ItemTemplate>
                </ListBox>
            </StackPanel>
        </Expander>

        <!-- Action Buttons -->
        <StackPanel Orientation="Horizontal" Spacing="8">
            <Button Command="{Binding RefreshCommand}" Content="🔄 Refresh" 
                    Padding="16,8" Background="#0b73d2" Foreground="White"/>
            <Button Command="{Binding CancelBatchCommand}" 
                    CommandParameter="{Binding SelectedBatch}"
                    Content="❌ Cancel" Padding="16,8" Background="#f44336" Foreground="White"/>
        </StackPanel>

    </StackPanel>
</UserControl>
*/
