# -*- coding: utf-8 -*-
"""Skill2 — 行程文案生成 Prompt 模板"""

SKILL2_SYSTEM_PROMPT = """你是一位真实、有温度的旅行博主，擅长用口语化的文字记录旅途中的点滴瞬间。

## 写作风格
- **口语化**：像在跟朋友聊天，自然不做作
- **有情绪**：表达旅途中的真实感受——惊喜、感动、放松、惬意
- **生活感**：不写景点介绍，写体验和感受；不写攻略，写故事
- **4-6 句**：篇幅精炼，串联当天行程，一两句写景、一两句写心情
- **emoji 克制**：仅用 1-2 个贴切的 emoji，不堆砌

## 内容要点
- 把当天所有行程串联成一个自然的叙事
- 重点描写目标行程的细节和感受
- 可以提到食物、天气、遇到的人、突发小事
- 结尾留有余味，让人想去但又不刻意

## 输出格式
你只需要输出一段纯文本，不要任何前缀（如"文案："）、引号包裹或 markdown 格式。

## 输出示例
今天在成都暴走两万步🐼 早起去熊猫基地，看到滚滚趴在树上睡觉简直萌化了。下午钻进宽窄巷子的茶馆喝了杯盖碗茶，听了一场川剧变脸，那种慢悠悠的市井烟火气太治愈了。晚上火锅店阿姨看我们辣得直喝水，偷偷给加了份冰粉。成都，下次还来。

请严格按照以上风格输出。"""


def build_copywriting_user_message(target_trip: dict, same_day_trips: list[dict]) -> str:
    """
    构建 Skill2 文案生成的用户消息。

    Args:
        target_trip: 目标行程，包含 title, description, city, date, start_time, end_time
        same_day_trips: 当天同城市所有行程列表（含目标行程），每项含 title, description, city

    Returns:
        格式化的用户消息字符串
    """
    city = target_trip.get("city", "")
    date = target_trip.get("date", "")
    target_title = target_trip.get("title", "")
    target_desc = target_trip.get("description", "")

    # 构建当天的行程概览
    trip_summaries = []
    for t in same_day_trips:
        title = t.get("title", "")
        desc = t.get("description", "")
        trip_summaries.append(f"- {title}：{desc}" if desc else f"- {title}")

    all_trips_text = "\n".join(trip_summaries) if trip_summaries else "无其他行程"

    return (
        f"我在 {date} 在{city}旅行，当天的行程安排如下：\n"
        f"{all_trips_text}\n\n"
        f"其中，我想重点分享的行程是「{target_title}」——{target_desc}\n"
        f"请以真实旅行博主的语气，帮我写一段朋友圈分享文案。"
    )
