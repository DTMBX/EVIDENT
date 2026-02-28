/**
 * VIDEO BATCH PROCESSOR - Mobile UI Component Library (Flutter/Dart)
 * Touch-optimized video upload, processing, transcription, and sync
 * 
 * Architecture: Flutter widgets, state management with Provider/Riverpod
 * Platforms: iOS, Android
 */

import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:file_picker/file_picker.dart';
import 'package:socket_io_client/socket_io_client.dart' as IO;
import 'dart:async';

// ======================== DESIGN TOKENS ========================

class DesignTokens {
  static const String primaryColor = '#0b73d2';
  static const String accentColor = '#e07a5f';
  static const String neutralColor = '#f6f7f9';
  static const String darkColor = '#1a1a1a';
  static const String successColor = '#4caf50';
  static const String warningColor = '#ff9800';
  static const String errorColor = '#f44336';

  static const double spacingXS = 4.0;
  static const double spacingSM = 8.0;
  static const double spacingMD = 16.0;
  static const double spacingLG = 24.0;
  static const double spacingXL = 32.0;

  static const double fontSizeBody = 14.0;
  static const double fontSizeHeading = 20.0;
  static const double fontSizeLarge = 24.0;

  static const String fontFamily = 'Roboto';
}

// ======================== PROGRESS BAR WIDGET ========================

class ProgressBarWidget extends StatelessWidget {
  final double progress;
  final String? label;

  const ProgressBarWidget({
    Key? key,
    required this.progress,
    this.label,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null)
          Text(
            label!,
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
        const SizedBox(height: 8),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: progress / 100,
            minHeight: 24,
            backgroundColor: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))),
            valueColor: AlwaysStoppedAnimation<Color>(
              Color(int.parse('0xff' + DesignTokens.primaryColor.replaceFirst('#', ''))),
            ),
            semanticsLabel: '${progress.toStringAsFixed(0)}%',
          ),
        ),
        const SizedBox(height: 8),
        Text(
          '${progress.toStringAsFixed(0)}%',
          style: const TextStyle(
            fontSize: DesignTokens.fontSizeBody,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

// ======================== FILE UPLOAD WIDGET ========================

class FileUploadWidget extends StatefulWidget {
  final Function(List<PlatformFile>) onFilesSelected;
  final bool multiple;
  final int maxFiles;

  const FileUploadWidget({
    Key? key,
    required this.onFilesSelected,
    this.multiple = true,
    this.maxFiles = 50,
  }) : super(key: key);

  @override
  State<FileUploadWidget> createState() => _FileUploadWidgetState();
}

class _FileUploadWidgetState extends State<FileUploadWidget> {
  List<PlatformFile> selectedFiles = [];

  Future<void> _pickFiles() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.video,
      allowMultiple: widget.multiple,
    );

    if (result != null) {
      final files = result.files.take(widget.maxFiles).toList();
      setState(() => selectedFiles = files);
      widget.onFilesSelected(files);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;
    
    return GestureDetector(
      onTap: _pickFiles,
      child: Container(
        padding: EdgeInsets.all(DesignTokens.spacingLG),
        decoration: BoxDecoration(
          border: Border.all(
            color: Color(int.parse('0xff' + DesignTokens.primaryColor.replaceFirst('#', ''))),
            width: 2,
            style: BorderStyle.solid,
          ),
          borderRadius: BorderRadius.circular(8),
          color: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))).withOpacity(0.3),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              '📹',
              style: TextStyle(fontSize: 32),
            ),
            const SizedBox(height: 16),
            Text(
              selectedFiles.isEmpty
                  ? 'Tap to select videos'
                  : '${selectedFiles.length} video(s) selected',
              style: const TextStyle(
                fontSize: DesignTokens.fontSizeHeading,
                fontWeight: FontWeight.w600,
                color: Color(0xff0b73d2),
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Up to ${widget.maxFiles} files (.mp4, .mov, .avi)',
              style: TextStyle(
                fontSize: 12,
                color: Color(int.parse('0xff' + DesignTokens.darkColor.replaceFirst('#', ''))),
              ),
            ),
            if (selectedFiles.isNotEmpty) ...[
              const SizedBox(height: 16),
              ListView.builder(
                shrinkWrap: true,
                itemCount: selectedFiles.length,
                itemBuilder: (context, index) {
                  final file = selectedFiles[index];
                  final sizeInMB = (file.size / 1024 / 1024).toStringAsFixed(1);
                  return Padding(
                    padding: EdgeInsets.symmetric(vertical: DesignTokens.spacingXS),
                    child: Text(
                      '✓ ${file.name} ($sizeInMB MB)',
                      style: const TextStyle(fontSize: 12),
                    ),
                  );
                },
              ),
            ],
          ],
        ),
      ),
    );
  }
}

// ======================== BATCH UPLOAD FORM ========================

class BatchUploadFormWidget extends StatefulWidget {
  final Function(Map<String, dynamic>) onSubmit;

  const BatchUploadFormWidget({
    Key? key,
    required this.onSubmit,
  }) : super(key: key);

  @override
  State<BatchUploadFormWidget> createState() => _BatchUploadFormWidgetState();
}

class _BatchUploadFormWidgetState extends State<BatchUploadFormWidget> {
  List<PlatformFile> files = [];
  final _caseIdController = TextEditingController();
  String quality = 'high';
  bool syncBwc = true;
  bool transcription = true;
  bool loading = false;

  void _handleSubmit() async {
    if (files.isEmpty || _caseIdController.text.isEmpty) return;

    setState(() => loading = true);

    try {
      widget.onSubmit({
        'files': files,
        'caseId': _caseIdController.text,
        'quality': quality,
        'syncBwc': syncBwc,
        'transcription': transcription,
      });

      // Reset form
      setState(() {
        files = [];
        _caseIdController.clear();
        quality = 'high';
        syncBwc = true;
        transcription = true;
      });
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Container(
        padding: EdgeInsets.all(DesignTokens.spacingLG),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '🎬 Batch Upload',
              style: const TextStyle(
                fontSize: DesignTokens.fontSizeLarge,
                fontWeight: FontWeight.w600,
                color: Color(0xff0b73d2),
              ),
            ),
            SizedBox(height: DesignTokens.spacingLG),

            // File Upload
            FileUploadWidget(
              onFilesSelected: (selectedFiles) {
                setState(() => files = selectedFiles);
              },
            ),
            SizedBox(height: DesignTokens.spacingLG),

            // Case ID
            Text(
              '📋 Case ID',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            SizedBox(height: DesignTokens.spacingSM),
            TextField(
              controller: _caseIdController,
              decoration: InputDecoration(
                hintText: 'e.g., case_2026_001',
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(4),
                ),
                contentPadding: EdgeInsets.all(DesignTokens.spacingMD),
              ),
            ),
            SizedBox(height: DesignTokens.spacingLG),

            // Quality
            Text(
              '⚙️ Quality',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            SizedBox(height: DesignTokens.spacingSM),
            DropdownButton<String>(
              value: quality,
              isExpanded: true,
              items: const [
                DropdownMenuItem(
                  value: 'ultra_low',
                  child: Text('Ultra Low (240p) - Fastest'),
                ),
                DropdownMenuItem(
                  value: 'low',
                  child: Text('Low (480p) - Mobile'),
                ),
                DropdownMenuItem(
                  value: 'medium',
                  child: Text('Medium (720p) - Balanced'),
                ),
                DropdownMenuItem(
                  value: 'high',
                  child: Text('High (1080p) - HD Evidence'),
                ),
                DropdownMenuItem(
                  value: 'ultra_high',
                  child: Text('Ultra High (4K) - Archive'),
                ),
              ],
              onChanged: (value) => setState(() => quality = value ?? 'high'),
            ),
            SizedBox(height: DesignTokens.spacingLG),

            // Options
            CheckboxListTile(
              title: const Text('🎤 Extract Transcription (Whisper)'),
              value: transcription,
              onChanged: (value) => setState(() => transcription = value ?? false),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            CheckboxListTile(
              title: const Text('📹 Auto-Sync Multiple Cameras'),
              value: syncBwc,
              onChanged: (value) => setState(() => syncBwc = value ?? false),
              controlAffinity: ListTileControlAffinity.leading,
            ),
            SizedBox(height: DesignTokens.spacingLG),

            // Submit Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: (files.isNotEmpty && _caseIdController.text.isNotEmpty && !loading)
                    ? _handleSubmit
                    : null,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Color(int.parse('0xff' + DesignTokens.primaryColor.replaceFirst('#', ''))),
                  padding: EdgeInsets.symmetric(vertical: DesignTokens.spacingMD),
                ),
                child: loading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(
                        '✓ Upload ${files.length} Video(s)',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: DesignTokens.fontSizeHeading,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _caseIdController.dispose();
    super.dispose();
  }
}

// ======================== BATCH PROGRESS MONITOR ========================

class BatchProgressMonitorWidget extends StatefulWidget {
  final String batchId;
  final VoidCallback onClose;

  const BatchProgressMonitorWidget({
    Key? key,
    required this.batchId,
    required this.onClose,
  }) : super(key: key);

  @override
  State<BatchProgressMonitorWidget> createState() => _BatchProgressMonitorWidgetState();
}

class _BatchProgressMonitorWidgetState extends State<BatchProgressMonitorWidget> {
  late IO.Socket socket;
  Map<String, dynamic>? status;
  List<Map<String, dynamic>> files = [];
  Map<String, dynamic>? syncStatus;
  bool connected = false;

  @override
  void initState() {
    super.initState();
    _connectWebSocket();
  }

  void _connectWebSocket() {
    socket = IO.io(
      'http://localhost:5000',
      IO.OptionBuilder()
          .setTransport(['websocket', 'polling'])
          .enableForceNew()
          .enableAutoConnect()
          .build(),
    );

    socket.onConnect((_) {
      setState(() => connected = true);
      socket.emit('subscribe_batch', {'batch_id': widget.batchId});
    });

    socket.on('batch_status', (data) {
      setState(() => status = data);
    });

    socket.on('batch_progress', (data) {
      setState(() => status = data);
    });

    socket.on('file_processed', (data) {
      setState(() {
        files.add({...data, 'status': 'complete'});
      });
    });

    socket.on('sync_progress', (data) {
      setState(() => syncStatus = data);
    });

    socket.onDisconnect((_) {
      setState(() => connected = false);
    });
  }

  double _calculateProgress() {
    if (status == null || status!['progress'] == null) return 0;
    final progressStr = status!['progress'] as String; // "5 / 10"
    final parts = progressStr.split('/').map((e) => int.parse(e.trim())).toList();
    if (parts.length == 2 && parts[1] > 0) {
      return (parts[0] / parts[1]) * 100;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context) {
    final progress = _calculateProgress();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Header
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(
                '📊 Processing: ${widget.batchId.substring(0, 8)}...',
                style: const TextStyle(
                  fontSize: DesignTokens.fontSizeHeading,
                  fontWeight: FontWeight.w600,
                  color: Color(0xff0b73d2),
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: widget.onClose,
            ),
          ],
        ),
        const SizedBox(height: 16),

        // Connection Status
        if (!connected)
          Container(
            padding: EdgeInsets.symmetric(
              horizontal: DesignTokens.spacingMD,
              vertical: DesignTokens.spacingSM,
            ),
            decoration: BoxDecoration(
              color: Color(int.parse('0xff' + DesignTokens.warningColor.replaceFirst('#', ''))),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Text(
              '⚠️ Connecting...',
              style: TextStyle(color: Colors.white),
            ),
          ),

        // Overall Progress
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Overall Progress',
              style: TextStyle(fontWeight: FontWeight.w600),
            ),
            Text(
              status?['progress'] ?? '0 / 0',
              style: const TextStyle(
                color: Color(0xff0b73d2),
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        ProgressBarWidget(progress: progress),

        // Sync Status
        if (syncStatus != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: EdgeInsets.all(DesignTokens.spacingMD),
            decoration: BoxDecoration(
              color: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '📹 Multi-Camera Synchronization',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                Text('✓ Total Videos: ${syncStatus!['total_videos']}'),
                Text('✓ Synced: ${syncStatus!['synced_videos']}/${syncStatus!['total_videos']}'),
                Text('✓ Confidence: ${syncStatus!['progress_percent'] ?? 0}%'),
              ],
            ),
          ),
        ],

        // File List
        if (files.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text(
            '📁 Files (${files.length})',
            style: const TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: files.length,
            itemBuilder: (context, index) {
              final file = files[index];
              return Container(
                padding: EdgeInsets.symmetric(vertical: DesignTokens.spacingSM),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))),
                    ),
                  ),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        file['id'].toString().substring(0, 12),
                        style: const TextStyle(fontSize: 12),
                      ),
                    ),
                    Container(
                      padding: EdgeInsets.symmetric(
                        horizontal: DesignTokens.spacingSM,
                        vertical: DesignTokens.spacingXS,
                      ),
                      decoration: BoxDecoration(
                        color: file['status'] == 'complete'
                            ? Color(int.parse('0xff' + DesignTokens.successColor.replaceFirst('#', '')))
                            : Color(int.parse('0xff' + DesignTokens.warningColor.replaceFirst('#', ''))),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        file['status'] == 'complete' ? '✓ Done' : '⏳ Processing',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],

        // Status
        const SizedBox(height: 16),
        Container(
          padding: EdgeInsets.all(DesignTokens.spacingMD),
          decoration: BoxDecoration(
            color: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Row(
            children: [
              const Text(
                'Status: ',
                style: TextStyle(fontWeight: FontWeight.w600),
              ),
              Text(
                status?['status'] == 'complete' ? '✓ Complete' : '⏳ In Progress',
                style: const TextStyle(
                  color: Color(0xff0b73d2),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    socket.dispose();
    super.dispose();
  }
}

// ======================== MAIN APP SCREEN ========================

class VideoBatchProcessorScreen extends StatefulWidget {
  @override
  State<VideoBatchProcessorScreen> createState() =>
      _VideoBatchProcessorScreenState();
}

class _VideoBatchProcessorScreenState extends State<VideoBatchProcessorScreen> {
  String? currentBatchId;
  List<String> batchHistory = [];

  void _handleUpload(Map<String, dynamic> uploadData) async {
    // Simulate batch creation
    final batchId = 'batch_${DateTime.now().millisecondsSinceEpoch}';
    setState(() {
      currentBatchId = batchId;
      batchHistory.insert(0, batchId);
    });

    // TODO: Send to API endpoint
    print('Uploading batch: $uploadData');
  }

  @override
  Widget build(BuildContext context) {
    final isMobile = MediaQuery.of(context).size.width < 600;

    return Scaffold(
      appBar: AppBar(
        title: const Text('🎥 Video Batch Processor'),
        backgroundColor: Color(int.parse('0xff0b73d2')),
      ),
      body: SingleChildScrollView(
        child: Container(
          color: Color(int.parse('0xff' + DesignTokens.neutralColor.replaceFirst('#', ''))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Container(
                padding: EdgeInsets.all(DesignTokens.spacingLG),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '🎥 Video Batch Processing',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w600,
                        color: Color(0xff0b73d2),
                      ),
                    ),
                    SizedBox(height: DesignTokens.spacingSM),
                    const Text(
                      'Upload, transcribe, and sync multiple videos in parallel',
                      style: TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),

              // Main Content
              Container(
                padding: EdgeInsets.all(DesignTokens.spacingLG),
                child: Column(
                  children: [
                    // Upload Form
                    Card(
                      child: BatchUploadFormWidget(onSubmit: _handleUpload),
                    ),
                    SizedBox(height: DesignTokens.spacingLG),

                    // Current Progress
                    if (currentBatchId != null)
                      Card(
                        child: Padding(
                          padding: EdgeInsets.all(DesignTokens.spacingLG),
                          child: BatchProgressMonitorWidget(
                            batchId: currentBatchId!,
                            onClose: () {
                              setState(() => currentBatchId = null);
                            },
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ======================== MAIN APP ENTRY ========================

void main() {
  runApp(const VideoBatchProcessorApp());
}

class VideoBatchProcessorApp extends StatelessWidget {
  const VideoBatchProcessorApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Video Batch Processor',
      theme: ThemeData(
        primaryColor: Color(int.parse('0xff0b73d2')),
        useMaterial3: true,
      ),
      home: VideoBatchProcessorScreen(),
    );
  }
}
