import random
from typing import List, Dict, Optional, Tuple

CARD_IMAGES = {
    '♥': 'https://deckofcardsapi.com/static/img/{}H.png',
    '♦': 'https://deckofcardsapi.com/static/img/{}D.png',
    '♣': 'https://deckofcardsapi.com/static/img/{}C.png',
    '♠': 'https://deckofcardsapi.com/static/img/{}S.png'
}

RANK_MAP = {
    '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
    '7': '7', '8': '8', '9': '9', '10': '0',
    'J': 'J', 'Q': 'Q', 'K': 'K', 'A': 'A'
}

class BlackjackGame:
    def __init__(self, player_id: int) -> None:
        self.player_id: int = player_id
        self.deck: List[Dict[str, str]] = self._create_deck()
        random.shuffle(self.deck)
        self.player_hand: List[Dict[str, str]] = []
        self.dealer_hand: List[Dict[str, str]] = []
        self.finished: bool = False
        self.winner: Optional[str] = None
        self.player_score: int = 0
        self.dealer_score: int = 0
        self.last_player_card: Optional[str] = None
        self.last_dealer_card: Optional[str] = None
        self.start_player_card: Optional[str] = None

        for _ in range(2):
            self.player_hand.append(self._draw_card())
            self.dealer_hand.append(self._draw_card())

        self.start_player_card = self._card_image(self.player_hand[0])
        self.player_score = self._hand_value(self.player_hand)
        self.dealer_score = self._hand_value(self.dealer_hand)

    def _create_deck(self) -> List[Dict[str, str]]:
        suits = ['♥', '♦', '♣', '♠']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [{'rank': r, 'suit': s} for s in suits for r in ranks]

    def _draw_card(self) -> Dict[str, str]:
        return self.deck.pop()

    def _card_image(self, card: Dict[str, str]) -> str:
        rank = RANK_MAP.get(card['rank'], card['rank'])
        suit = card['suit']
        return CARD_IMAGES[suit].format(rank)

    def _hand_value(self, hand: List[Dict[str, str]]) -> int:
        value: int = 0
        aces: int = 0
        for card in hand:
            rank: str = card['rank']
            if rank.isdigit():
                value += int(rank)
            elif rank in ['J', 'Q', 'K']:
                value += 10
            else:
                aces += 1
                value += 11
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        return value

    def _is_bust(self, hand: List[Dict[str, str]]) -> bool:
        return self._hand_value(hand) > 21

    def player_turn(self, action: str):
        if self.finished:
            return "Игра уже закончена.", self.player_score, self.dealer_score, None, None

        if action == "hit":
            self.player_hand.append(self._draw_card())
            self.player_score = self._hand_value(self.player_hand)
            self.last_player_card = self._card_image(self.player_hand[-1])
            if self._is_bust(self.player_hand):
                self.finished = True
                self.winner = "dealer"
                return f"💥 Перебор! Ты проиграл.", self.player_score, self.dealer_score, self.last_player_card, None
            return f"✅ Ты взял карту.", self.player_score, self.dealer_score, self.last_player_card, None

        elif action == "stand":
            self.finished = True
            return self._dealer_turn()

        return "Неизвестное действие.", self.player_score, self.dealer_score, None, None

    def _dealer_turn(self):
        while self._hand_value(self.dealer_hand) < 17:
            self.dealer_hand.append(self._draw_card())
            self.last_dealer_card = self._card_image(self.dealer_hand[-1])

        self.player_score = self._hand_value(self.player_hand)
        self.dealer_score = self._hand_value(self.dealer_hand)

        if self._is_bust(self.dealer_hand):
            self.winner = "player"
            return f"🎉 Дилер перебрал! Ты выиграл!", self.player_score, self.dealer_score, None, self.last_dealer_card
        elif self.dealer_score > self.player_score:
            self.winner = "dealer"
            return f"😞 Дилер выиграл.", self.player_score, self.dealer_score, None, self.last_dealer_card
        elif self.player_score > self.dealer_score:
            self.winner = "player"
            return f"🎉 Ты выиграл!", self.player_score, self.dealer_score, None, self.last_dealer_card
        else:
            self.winner = "tie"
            return f"🤝 Ничья!", self.player_score, self.dealer_score, None, self.last_dealer_card

    def get_status(self) -> str:
        if self.finished:
            return "Игра закончена."
        return f"**Твои карты:** {len(self.player_hand)} карт — {self.player_score} очков\n**Карты дилера:** {len(self.dealer_hand)} карт (1 скрыта)"

    def get_start_card(self) -> str:
        return self.start_player_card

    def get_player_cards_text(self) -> str:
        return " ".join([f"{c['rank']}{c['suit']}" for c in self.player_hand])

    def get_dealer_cards_text(self, hide_first: bool = True) -> str:
        if hide_first:
            return f"{self.dealer_hand[0]['rank']}{self.dealer_hand[0]['suit']} 🂠"
        return " ".join([f"{c['rank']}{c['suit']}" for c in self.dealer_hand])

    def get_all_player_images(self) -> List[str]:
        return [self._card_image(c) for c in self.player_hand]

    def get_last_player_image(self) -> Optional[str]:
        if self.player_hand:
            return self._card_image(self.player_hand[-1])
        return None
