#pragma once

#include "framework.h"

#define SUPPORT_VERSION L"3.9.12.57"

// 自定义消息ID，用于DLL与外部程序通信
#define WM_WECHAT_MESSAGE (WM_USER + 1001)

static char* baseUrl;

void InitSpy(LPVOID args);
void CleanupSpy();
