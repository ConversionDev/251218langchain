import 'package:flutter/material.dart';

void main() {
  runApp(const RAGMobileApp());
}

class RAGMobileApp extends StatelessWidget {
  const RAGMobileApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'RAG Mobile App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: Scaffold(
        backgroundColor: Colors.grey.shade100,
        body: Builder(
          builder: (context) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  '애뮬레이터 테스트',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 24),
                OutlinedButton.icon(
                  onPressed: () {
                    showDialog(
                      context: context,
                      builder: (ctx) => AlertDialog(
                        content: const Text('로그인 실행'),
                        actions: [
                          TextButton(
                            onPressed: () => Navigator.of(ctx).pop(),
                            child: const Text('확인'),
                          ),
                        ],
                      ),
                    );
                  },
                  icon: const Icon(Icons.g_mobiledata),
                  label: const Text('Google로 로그인'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
