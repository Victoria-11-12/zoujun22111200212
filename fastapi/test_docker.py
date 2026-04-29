import os

# Windows Docker 连接配置，必须在 import docker 之前设置
os.environ['DOCKER_HOST'] = 'npipe:////./pipe/docker_engine'

import docker

print(f"[Test] DOCKER_HOST env: {os.environ.get('DOCKER_HOST', 'NOT SET')}")

try:
    # 测试1: 使用 docker.from_env()
    print("\n[Test] Testing docker.from_env()...")
    client1 = docker.from_env()
    print(f"[Test] docker.from_env() success: {client1.version()}")
except Exception as e:
    print(f"[Test] docker.from_env() failed: {e}")

try:
    # 测试2: 使用 docker.DockerClient 直接指定 base_url
    print("\n[Test] Testing docker.DockerClient(base_url='npipe:////./pipe/docker_engine')...")
    client2 = docker.DockerClient(base_url='npipe:////./pipe/docker_engine')
    print(f"[Test] docker.DockerClient() success: {client2.version()}")
except Exception as e:
    print(f"[Test] docker.DockerClient() failed: {e}")

try:
    # 测试3: 使用 docker.DockerClient 直接指定 tcp
    print("\n[Test] Testing docker.DockerClient(base_url='tcp://localhost:2375')...")
    client3 = docker.DockerClient(base_url='tcp://localhost:2375')
    print(f"[Test] tcp://localhost:2375 success: {client3.version()}")
except Exception as e:
    print(f"[Test] tcp://localhost:2375 failed: {e}")

print("\n[Test] All tests completed.")
