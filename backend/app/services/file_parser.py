import asyncio
import io
import pandas as pd


class FileParserService:
    @staticmethod
    def parse_tabular_data(file_bytes: bytes, filename: str) -> str:
        """Parse CSV/XLSX synchronously (fast enough, called from async context via to_thread)."""
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
                except Exception:
                    try:
                        df = pd.read_csv(io.BytesIO(file_bytes), skiprows=3, encoding='utf-8')
                    except Exception:
                        df = pd.read_csv(io.BytesIO(file_bytes), skiprows=3, encoding='gbk')

            data_summary = (
                f"\n\n[系统已解析表格数据]\n文件名：{filename}\n数据规模：{df.shape[0]}行 {df.shape[1]}列\n"
                f"【表头及前5行】:\n{df.head(5).to_string()}\n"
                f"【统计摘要】:\n{df.describe().to_string()}\n"
            )
            return data_summary
        except Exception as e:
            return f"\n\n[文件 {filename} 解析失败: {str(e)}]"

    @staticmethod
    async def parse_tabular_data_async(file_bytes: bytes, filename: str) -> str:
        """Run the synchronous parser in a thread to avoid blocking the event loop."""
        return await asyncio.to_thread(FileParserService.parse_tabular_data, file_bytes, filename)
