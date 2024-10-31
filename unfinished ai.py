# Function to call OpenAI's API
def call_openai(prompt, model):
  response = openai.Completion.create(engine=model,
                                      prompt=prompt,
                                      max_tokens=150,
                                      temperature=0.7,
                                      top_p=1,
                                      frequency_penalty=0,
                                      presence_penalty=0)
  print(response)
  return response.choices[0].text.strip()


# Function to call OpenAI's API
def call_openai(prompt, model):
  response = openai.Completion.create(engine=model, prompt=prompt, max_tokens=150,
                                          temperature=0.7, top_p=1, frequency_penalty=0, presence_penalty=0)
  return response.choices[0].text.strip()

# Main function to process queries
async def process_query(messages, image_path=None):
  if image_path:
    # If there's an image, encode it and prepare the message
    encoded_image = encode_image(image_path)
    messages.append({"role": "system", "content": f"data:image/jpeg;base64,{encoded_image}"})

  # Prepare payload for ND API
  payload = json.dumps({"messages": messages, "fallback_model": "gpt-3.5-turbo"})
  headers = {"Authorization": f"Bearer {ND_API_KEY}", "Content-Type": "application/json"}

  # Make request to ND API
  response = requests.post("https://not-diamond-backend.onrender.com/modelSelector/", headers=headers, data=payload).json()
  model = response.get("model", "gpt-3.5-turbo")
  response.get("token_estimate")

  # Select the appropriate model based on the ND API's response
  openai_model = "gpt-3.5-turbo-1106"  # default
  if model == "gpt-3.5":
    openai_model = "gpt-3.5-turbo-1106"  # GPT-3.5 (Standard)
  elif model == "gpt-4" and image_path is None:
    openai_model = "gpt-4-1106-preview"  # GPT-4 (Turbo)
  elif model == "gpt-4" and image_path is not None:
    openai_model = "gpt-4-1106-vision-preview"  # GPT-4 Vision (Turbo Vision)

  # Retrieve the current conversation from the database
  guild_id = messages[0]['guild_id']
  user_id = messages[0]['user_id']
  get_messages(guild_id, user_id)

  # Add the new message to the conversation and save it
  save_message(guild_id, user_id, messages[-1])

  # Create the prompt from the conversation history
  prompt = " ".join(msg['content'] for msg in messages)
  response_text = call_openai(prompt, openai_model)

  return response_text, openai_model


def check_points(user_id):
  print("Checking points...")
  return db.get(f"points_{user_id}", 0)


def update_points(user_id, points):
  current_points = check_points(user_id)
  new_points = max(current_points + points, 0)
  db[f"points_{user_id}"] = new_points
  print("Updated points for user", user_id, "to", new_points)

ai_explanation = """
***Info:***
Interacts with an advanced AI to simulate conversation or answer queries. Costs points based on the complexity and model used.
Your queries will be processed based on its complexity, then sent to an approriate model.
If an image is sent, it will automatically use the Turbo GPT-4 Vision model.
- Normal conversation maintains context for a more coherent interaction.
- Optional flag `-s` for a standalone query without context, which costs fewer points.

**Usage:** 
`7/ai "<message>"` (Engages in a contextual conversation. Costs more points based on the AI model used.)
`7/ai "<message>" -s` (Engages in a standalone query without considering conversation history. Costs fewer points.)

**Examples:**
`7/ai "What is the capital of France?"` (Contextual conversation)
`7/ai "What is the capital of France?" -s` (Standalone query)

***Cost:***
- **GPT-3.5 (Standard)**: 10 points per use.
- **GPT-4 (Turbo)**: 20 points per use.
- **GPT-4 Vision (Turbo Vision)**: 30 points per use.
- **Discount for '-s' flag**: 50% off the above prices.

***Tips:***
- Use the `-s` flag for quick queries when you don't need the context of a conversation. It saves your points.
- Ensure you have enough points before using the command. You can earn points by participating in the server and using other features.
- The AI's response quality and understanding may vary based on the auto-selected model by the complexity of your query.
"""

@bot.command(name="ai", usage="7/ai <message> <optional flag: -s>", aliases=["ai_bot"], help=ai_explanation)
async def ai_command(ctx, *, message: str):
  print(message)
  user_id = str(ctx.author.id)
  guild_id = str(ctx.guild.id)
  standalone = '-s' in message
  message_content = message.replace('-s', '').strip()
  if message is None:
    await ctx.send("Invalid usage. For detailed help, type: `7/ai help`")
  elif message.lower() == "help":
    embed = discord.Embed(title="AI Command",
                          description=ai_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  # Define the base cost for each model
  model_costs = {
      'text-davinci-003': 10,  # GPT-3.5 cost
      'gpt-4-1106-preview': 20,  # GPT-4 cost
      'gpt-4-1106-vision-preview': 30  # GPT-4 Vision cost
  }

  conversation = get_messages(guild_id, user_id)

  if standalone:
    # If standalone, don't consider historical context
    response, model_used = await process_query([{
    "role": "user",
    "content": message_content
  }])
    print("s")
  else:
    print("n-s")
    conversation.append({"role": "user", "content": message_content})
    save_message(guild_id, user_id, {
      "role": "user",
      "content": message_content
    })

    response, model_used = await process_query(conversation)
    print(response)
  # Determine the cost based on the model used
  cost = model_costs.get(model_used,
                         10)  # Default to 10 points if the model isn't found

  # Discount for standalone queries
  if standalone:
    cost = int(cost * 0.5)  # 50% discount for standalone queries

  user_points = check_points(user_id)

  if user_points >= cost:
    update_points(user_id, -cost)  # Deduct the cost from the user's points
    await ctx.send(response)
  else:
    await ctx.send(
        f"You don't have enough points for this operation. This operation costs {cost} points, but you only have {user_points}."
    )
