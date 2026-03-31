#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Garmin Token 测试脚本 - 测试 garth 认证功能
"""

import os
import sys

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from scripts.garmin.garmin_client import GarminClient


def test_login_and_save():
    """测试登录并保存 token"""
    print("\n=== 测试登录并保存 Token ===")

    email = input("请输入测试账号邮箱：")
    password = input("请输入测试账号密码：")

    client = GarminClient(
        email=email,
        password=password,
        auth_domain="COM",
        newest_num=10,
    )

    result = client.login_and_save_token()

    if result:
        print("✓ 登录测试通过")
        return client
    else:
        print("✗ 登录测试失败")
        return None


def test_load_token():
    """测试加载 token"""
    print("\n=== 测试加载 Token ===")

    client = GarminClient(
        email="test@example.com",
        password="dummy",
        auth_domain="COM",
        newest_num=10,
    )

    result = client.load_token()

    if result:
        print("✓ Token 加载测试通过")
        return client
    else:
        print("✗ Token 加载测试失败")
        return None


def test_authenticate():
    """测试自动认证（优先 token，失败则登录）"""
    print("\n=== 测试自动认证 ===")

    email = input("请输入测试账号邮箱：")
    password = input("请输入测试账号密码：")

    client = GarminClient(
        email=email,
        password=password,
        auth_domain="COM",
        newest_num=10,
    )

    result = client.authenticate()

    if result:
        print("✓ 自动认证测试通过")
        return client
    else:
        print("✗ 自动认证测试失败")
        return None


def test_api_call(client):
    """测试 API 调用"""
    print("\n=== 测试 API 调用 ===")

    if not client:
        print("✗ 客户端未初始化")
        return

    try:
        # 获取用户信息
        profile = client.connectapi("/userprofile-service/socialProfile")
        if profile:
            print(f"✓ 用户信息获取成功")
            print(f"  用户 ID: {profile.get('id')}")
            print(f"  用户名：{profile.get('userName')}")
        else:
            print("✗ 未获取到用户信息")

        # 获取活动列表
        activities = client.getAllActivities()
        if activities:
            print(f"✓ 活动列表获取成功，共 {len(activities)} 条")
            if len(activities) > 0:
                first = activities[0]
                print(f"  最新活动 ID: {first.get('activityId')}")
                print(f"  类型：{first.get('activityType', {}).get('key')}")
        else:
            print("⚠ 未获取到活动数据")

    except Exception as e:
        print(f"✗ API 调用失败：{e}")


def main():
    """运行测试"""
    print("=" * 60)
    print("Garmin Token 功能测试 (基于 garth)")
    print("=" * 60)

    try:
        # 测试自动认证（推荐）
        client = test_authenticate()
        if client:
            # 测试 API 调用
            test_api_call(client)

            print("\n" + "=" * 60)
            print("✓ 所有测试完成！")
            print("=" * 60)
        else:
            print("\n✗ 认证失败，无法继续测试")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试异常：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # main()
    test_load_token()