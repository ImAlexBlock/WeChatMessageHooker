#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import win32gui
import win32con
import win32api
import json
import logging
import sys
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gateway.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class WeChatMessageGateway:
    def __init__(self):
        self.hwnd = None
        self.window_class_name = "WeChatMessageGateway"
        self.window_title = "WeChatMessageGateway"
        
    def wnd_proc(self, hwnd, msg, wparam, lparam):
        """窗口消息处理函数"""
        try:
            if msg == win32con.WM_COPYDATA:
                # 处理WM_COPYDATA消息
                return self._handle_copydata(hwnd, msg, wparam, lparam)
            elif msg == win32con.WM_DESTROY:
                # 窗口销毁消息
                win32gui.PostQuitMessage(0)
                return 0
        except Exception as e:
            logger.error(f"Error in wnd_proc: {e}")
            
        # 默认消息处理
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _handle_copydata(self, hwnd, msg, wparam, lparam):
        """处理WM_COPYDATA消息"""
        try:
            # 调试模式：直接打印收到的消息
            logger.debug(f"Received WM_COPYDATA message, lparam type: {type(lparam)}, value: {lparam}")
            
            # 如果lparam是一个整数，它应该是指向COPYDATASTRUCT结构的指针
            if isinstance(lparam, int):
                try:
                    # 尝试读取COPYDATASTRUCT结构（假设64位系统，结构大小为24字节）
                    # 结构包含：dwData(8字节), cbData(4字节), padding(4字节), lpData(8字节)
                    import struct
                    cds_data = win32gui.PyGetMemory(lparam, 24)
                    # 解析结构字段
                    dwData, cbData, padding, lpData = struct.unpack('QIIQ', cds_data)
                    
                    logger.debug(f"COPYDATASTRUCT parsed - dwData: {dwData}, cbData: {cbData}, lpData: {lpData}")
                    
                    # 读取实际数据
                    if cbData > 0 and lpData != 0:
                        try:
                            data_memory = win32gui.PyGetMemory(lpData, cbData)
                            # 将memoryview转换为bytes
                            if isinstance(data_memory, memoryview):
                                data_bytes = data_memory.tobytes()
                            else:
                                data_bytes = bytes(data_memory)
                            
                            logger.debug(f"Raw data length: {len(data_bytes)}, first 32 bytes (hex): {data_bytes[:32].hex()}")
                            
                            # 尝试多种解码方式
                            decoded_data = None
                            # 首先尝试UTF-8解码
                            try:
                                decoded_data = data_bytes.decode('utf-8')
                                logger.debug(f"Decoded as UTF-8: {decoded_data}")
                            except UnicodeDecodeError:
                                pass
                            
                            # 如果UTF-8失败，尝试GBK解码（中文Windows常用编码）
                            if decoded_data is None:
                                try:
                                    decoded_data = data_bytes.decode('gbk')
                                    logger.debug(f"Decoded as GBK: {decoded_data}")
                                except UnicodeDecodeError:
                                    pass
                            
                            # 如果GBK也失败，尝试Latin-1解码（不会抛出异常）
                            if decoded_data is None:
                                try:
                                    decoded_data = data_bytes.decode('latin-1')
                                    logger.debug(f"Decoded as Latin-1: {decoded_data}")
                                except UnicodeDecodeError:
                                    pass
                            
                            # 如果所有解码都失败，直接使用原始字节数据
                            if decoded_data is None:
                                logger.debug("Failed to decode data with any encoding")
                                decoded_data = data_bytes.decode('utf-8', errors='replace')
                                logger.debug(f"Decoded with replacement characters: {decoded_data}")
                            
                            # 移除可能的终止符
                            if decoded_data.endswith('\x00'):
                                decoded_data = decoded_data[:-1]
                                logger.debug("Removed null terminator")
                            
                            logger.debug(f"Final decoded data: {decoded_data}")
                            
                            # 解析JSON数据
                            try:
                                message_data = json.loads(decoded_data)
                                logger.info(f"Received message: {json.dumps(message_data, ensure_ascii=False, indent=2)}")
                                return 1  # 成功处理
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to parse JSON: {e}")
                                logger.error(f"Raw data: {decoded_data}")
                                # 仍然返回成功，因为我们收到了数据
                                return 1
                        except Exception as memory_error:
                            logger.error(f"Failed to read memory at lpData: {memory_error}")
                            # 尝试读取更小的数据块进行调试
                            try:
                                small_data = win32gui.PyGetMemory(lpData, min(cbData, 16))
                                # 将memoryview转换为bytes再转换为hex
                                if isinstance(small_data, memoryview):
                                    small_bytes = small_data.tobytes()
                                else:
                                    small_bytes = bytes(small_data)
                                logger.debug(f"First 16 bytes of data (hex): {small_bytes.hex()}")
                            except:
                                pass
                            return 0
                    else:
                        logger.warning("Empty data received")
                        return 1
                except Exception as struct_error:
                    logger.error(f"Failed to parse COPYDATASTRUCT: {struct_error}")
                    # 以十六进制形式打印lparam指向的内存
                    try:
                        mem_data = win32gui.PyGetMemory(lparam, 64)  # 尝试读取64字节
                        logger.debug(f"Memory at lparam (hex): {mem_data.hex()}")
                    except Exception as mem_error:
                        logger.error(f"Failed to read memory at lparam: {mem_error}")
                    return 0
            else:
                # 如果lparam不是一个整数，记录错误并返回
                logger.error(f"Unexpected lparam type: {type(lparam)}")
                return 0
                
        except Exception as e:
            logger.error(f"Error handling COPYDATA: {e}")
            logger.exception(e)  # 打印完整的异常堆栈
            return 0  # 处理失败
    
    def create_window(self):
        """创建消息接收窗口"""
        try:
            # 创建窗口类
            wc = win32gui.WNDCLASS()
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.lpszClassName = self.window_class_name
            wc.lpfnWndProc = self.wnd_proc
            
            # 注册窗口类
            class_atom = win32gui.RegisterClass(wc)
            if not class_atom:
                raise Exception("Failed to register window class")
                
            # 创建隐藏窗口
            self.hwnd = win32gui.CreateWindow(
                class_atom,
                self.window_title,
                win32con.WS_OVERLAPPEDWINDOW,
                0, 0, 0, 0,  # 位置和大小
                0,  # 父窗口
                0,  # 菜单
                wc.hInstance,
                None
            )
            
            if not self.hwnd:
                raise Exception("Failed to create window")
                
            logger.info(f"Gateway window created successfully, HWND: {self.hwnd}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create window: {e}")
            return False
    
    def run(self):
        """运行消息循环"""
        try:
            logger.info("WeChat Message Gateway started")
            logger.info("Waiting for messages from DLL...")
            
            # 消息循环
            win32gui.PumpMessages()
                    
        except KeyboardInterrupt:
            logger.info("Gateway interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.hwnd:
                win32gui.DestroyWindow(self.hwnd)
                logger.info("Gateway window destroyed")
        except Exception as e:
            logger.error(f"Error in cleanup: {e}")

def main():
    """主函数"""
    try:
        # 创建网关实例
        gateway = WeChatMessageGateway()
        
        # 创建窗口
        if not gateway.create_window():
            logger.error("Failed to create gateway window")
            return 1
            
        # 运行消息循环
        gateway.run()
        
        logger.info("WeChat Message Gateway stopped")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())