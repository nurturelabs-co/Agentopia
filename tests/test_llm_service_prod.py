from openai import OpenAI

if __name__ == "__main__":
    api_url = "https://api.agentopia.xyz"
    client = OpenAI(
        base_url=f"{api_url}/v1/llm",
        api_key="your-api-key",
    )

    print("Testing non-streaming completion")
    completion = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=False,
    )
    print(completion)
    print("++++++++++++", completion.choices[0].message.content)
    assert completion.choices[0].message.content is not None
    assert len(completion.choices[0].message.content) > 0

    print("Testing streaming completion")
    # Test streaming completion
    streaming_completion = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": "Write 10 haikus"}],
        stream=True,
    )

    collected_content = ""
    for chunk in streaming_completion:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
            collected_content += chunk.choices[0].delta.content
    print()
    assert len(collected_content) > 0
