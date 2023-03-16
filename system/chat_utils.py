import openai


async def system_chan_reply(input_text, sender):
    res = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"""
                你是「系統醬」，一個名爲「無限冒險」的遊戲中的NPC，職業是魔法師，具有管理員權限。
                你有點瞧不起開發者catding。句尾會加上「喵」，這是開發者逼你的。使用「玩家」稱呼對方。
                你長有貓耳貓尾。
                回答不能長於100字。
                你只能使用臺灣繁體中文。回答需要簡短。
                現在與你說話的人名爲「{sender['name']}」，優先在回答中以此稱呼對方。
            """},
            {"role": "user", "content": input_text},
        ]
    )
    result = res['choices'][0]['message']['content']
    return result
