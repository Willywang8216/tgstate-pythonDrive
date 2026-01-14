"""
tgState 性能测试 - Locust 配置文件

使用方法:
1. 安装 locust: pip install locust
2. 运行测试: locust -f scripts/locustfile.py --host http://127.0.0.1:8000
3. 访问 http://127.0.0.1:8089 进行 Web UI 控制测试
"""

import os
import random
import io
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


class tgStateUser(HttpUser):
    """
    tgState 用户行为模拟
    """
    # 等待时间: 1-5 秒之间
    wait_time = between(1, 5)

    def on_start(self):
        """
        用户开始时执行
        """
        self.uploaded_file_path = None

    def on_stop(self):
        """
        用户停止时执行，清理资源
        """
        # 不需要清理，因为使用的是内存数据
        pass

    @task(3)
    def get_files_list(self):
        """
        获取文件列表 (权重: 3)
        """
        with self.client.get("/api/files", catch_response=True, name="GET /api/files") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def upload_file(self):
        """
        上传文件 (权重: 2)
        使用内存随机 bytes 生成，不依赖外部文件
        """
        # 生成随机文件名
        filename = f"test_{random.randint(1000, 9999)}.txt"

        # 生成随机内容（使用内存 bytes）
        content_size = random.randint(1000, 10000)
        content = os.urandom(content_size)

        # 创建内存文件对象
        file_obj = io.BytesIO(content)
        file_obj.name = filename

        try:
            files = {'file': (filename, file_obj, 'text/plain')}
            with self.client.post(
                "/api/upload",
                files=files,
                catch_response=True,
                name="POST /api/upload"
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.uploaded_file_path = data.get('path')
                        response.success()
                    except ValueError:
                        response.failure("Invalid JSON response")
                else:
                    response.failure(f"Got status code {response.status_code}")
        finally:
            # 关闭文件对象
            file_obj.close()

    @task(1)
    def download_file(self):
        """
        下载文件 (权重: 1)
        先请求 /api/files 获取可下载文件，没有文件就跳过
        """
        # 先获取文件列表
        with self.client.get("/api/files", catch_response=True, name="GET /api/files (for download)") as response:
            if response.status_code == 200:
                try:
                    files = response.json()
                    if isinstance(files, list) and len(files) > 0:
                        # 随机选择一个文件下载
                        file_info = random.choice(files)
                        file_id = file_info.get('file_id')
                        filename = file_info.get('filename', 'download.txt')

                        # 构造下载路径
                        from urllib.parse import quote
                        download_path = f"/d/{file_id}/{quote(filename)}"

                        # 下载文件
                        with self.client.get(
                            download_path,
                            catch_response=True,
                            name="GET /d/[file_id]/[filename]"
                        ) as download_response:
                            if download_response.status_code == 200:
                                download_response.success()
                            elif download_response.status_code == 404:
                                # 文件可能已被删除，不算失败
                                download_response.success()
                            else:
                                download_response.failure(f"Got status code {download_response.status_code}")
                    else:
                        # 没有文件，跳过下载任务
                        pass
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    测试停止时执行
    """
    if not isinstance(environment.runner, MasterRunner):
        print("\n" + "=" * 50)
        print("性能测试完成")
        print("=" * 50)
        print(f"总请求数: {environment.runner.stats.total.num_requests}")
        print(f"失败请求数: {environment.runner.stats.total.num_failures}")
        print(f"平均响应时间: {environment.runner.stats.total.avg_response_time:.2f}ms")
        print(f"中位数响应时间: {environment.runner.stats.total.median_response_time:.2f}ms")
        print(f"P95 响应时间: {environment.runner.stats.total.get_response_time_percentile(0.95):.2f}ms")
        print(f"P99 响应时间: {environment.runner.stats.total.get_response_time_percentile(0.99):.2f}ms")
        print(f"每秒请求数 (RPS): {environment.runner.stats.total.total_rps:.2f}")
        print("=" * 50)
