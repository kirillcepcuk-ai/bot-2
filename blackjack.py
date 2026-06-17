import discord # pyright: ignore[reportMissingImports]
from discord.ext import commands # pyright: ignore[reportMissingImports]
from config import TOKEN, COLOR_GREEN, COLOR_RED, COLOR_GOLD, COLOR_PURPLE, COLOR_BLUE
from blackjack import BlackjackGame
import database as db

intents = discord.Intents.default()
intents.message_content = True
bot: commands.Bot = commands.Bot(command_prefix='/', intents=intents)

games: dict = {}

class BlackjackView(discord.ui.View):
    def __init__(self, game, user_id):
        super().__init__(timeout=60)
        self.game = game
        self.user_id = user_id

    @discord.ui.button(label="Взять карту", style=discord.ButtonStyle.green, custom_id="hit")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Не твоя игра", ephemeral=True)
            return

        result, player_score, dealer_score, player_image, dealer_image = self.game.player_turn("hit")
        
        if self.game.finished:
            del games[self.user_id]
            if self.game.winner == "player":
                db.update_player_stats(self.user_id, "win")
                db.save_game_history(self.user_id, "player", player_score, dealer_score)
                color = COLOR_GOLD
            elif self.game.winner == "dealer":
                db.update_player_stats(self.user_id, "loss")
                db.save_game_history(self.user_id, "dealer", player_score, dealer_score)
                color = COLOR_RED
            else:
                db.update_player_stats(self.user_id, "tie")
                db.save_game_history(self.user_id, "tie", player_score, dealer_score)
                color = COLOR_GREEN

            embed = discord.Embed(
                title="🃏 Блэкджек",
                description=result,
                color=color
            )
            embed.add_field(
                name="Твои карты",
                value=self.game.get_player_cards_text(),
                inline=False
            )
            embed.add_field(
                name="Карты дилера",
                value=self.game.get_dealer_cards_text(hide_first=False),
                inline=False
            )
            embed.set_footer(text=f"Твои очки: {player_score} | Дилер: {dealer_score}")
            if player_image:
                embed.set_image(url=player_image)
            await interaction.response.edit_message(embed=embed, view=None)
            return

        embed = discord.Embed(
            title="🃏 Блэкджек",
            description=f"{result}\n\n{self.game.get_status()}",
            color=COLOR_GREEN
        )
        embed.add_field(
            name="Твои карты",
            value=self.game.get_player_cards_text(),
            inline=False
        )
        if player_image:
            embed.set_image(url=player_image)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Остановиться", style=discord.ButtonStyle.red, custom_id="stand")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Не твоя игра", ephemeral=True)
            return

        result, player_score, dealer_score, player_image, dealer_image = self.game.player_turn("stand")
        del games[self.user_id]

        if self.game.winner == "player":
            db.update_player_stats(self.user_id, "win")
            db.save_game_history(self.user_id, "player", player_score, dealer_score)
            color = COLOR_GOLD
        elif self.game.winner == "dealer":
            db.update_player_stats(self.user_id, "loss")
            db.save_game_history(self.user_id, "dealer", player_score, dealer_score)
            color = COLOR_RED
        else:
            db.update_player_stats(self.user_id, "tie")
            db.save_game_history(self.user_id, "tie", player_score, dealer_score)
            color = COLOR_GREEN

        embed = discord.Embed(
            title="🃏 Блэкджек",
            description=result,
            color=color
        )
        embed.add_field(
            name="Твои карты",
            value=self.game.get_player_cards_text(),
            inline=False
        )
        embed.add_field(
            name="Карты дилера",
            value=self.game.get_dealer_cards_text(hide_first=False),
            inline=False
        )
        embed.set_footer(text=f"Твои очки: {player_score} | Дилер: {dealer_score}")
        if player_image:
            embed.set_image(url=player_image)
        await interaction.response.edit_message(embed=embed, view=None)

@bot.event
async def on_ready():
    db.init_db()
    print(f"✅ {bot.user} запущен")
    await bot.change_presence(activity=discord.Game(name="/bj"))
    await bot.tree.sync()
    print("✅ Команды готовы")

@bot.tree.command(name="bj", description="Начать игру в 21")
async def bj(interaction: discord.Interaction) -> None:
    if interaction.user.id in games:
        await interaction.response.send_message("❌ У тебя уже есть игра", ephemeral=True)
        return

    game: BlackjackGame = BlackjackGame(interaction.user.id)
    games[interaction.user.id] = game

    embed: discord.Embed = discord.Embed(
        title="🃏 Блэкджек",
        description=game.get_status(),
        color=COLOR_PURPLE
    )
    embed.add_field(
        name="Твои карты",
        value=game.get_player_cards_text(),
        inline=False
    )
    embed.set_image(url=game.get_start_card())
    embed.set_footer(text=f"Твои очки: {game.player_score} | Дилер: скрыто")
    
    view = BlackjackView(game, interaction.user.id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="stats", description="Моя статистика")
async def stats(interaction: discord.Interaction) -> None:
    stats_data = db.get_player_stats(interaction.user.id)

    embed = discord.Embed(
        title="📊 Моя статистика",
        description=f"**Всего игр:** {stats_data['total_games']}\n"
                    f"🏆 Побед: {stats_data['wins']}\n"
                    f"💀 Поражений: {stats_data['losses']}\n"
                    f"🤝 Ничьих: {stats_data['ties']}",
        color=COLOR_BLUE
    )
    embed.set_footer(text=f"Игрок: {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="history", description="Последние 5 игр")
async def history(interaction: discord.Interaction) -> None:
    rows = db.get_history(interaction.user.id, 5)

    if not rows:
        await interaction.response.send_message("📭 Нет сыгранных игр.", ephemeral=True)
        return

    description = ""
    for row in rows:
        winner, player_score, dealer_score, date = row
        emoji = "🏆" if winner == "player" else "💀" if winner == "dealer" else "🤝"
        description += f"{emoji} {winner.capitalize()} | Ты: {player_score} | Дилер: {dealer_score} | {date[:10]}\n"

    embed = discord.Embed(
        title="📜 История игр (последние 5)",
        description=description,
        color=COLOR_BLUE
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    bot.run(TOKEN)
