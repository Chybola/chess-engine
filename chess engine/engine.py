
"""Simple chess engine.

This version is intentionally small and easy to read.
It uses only standard Python features.
"""

from copy import deepcopy

from chess_board import Color, PieceType


class ChessEngine:
    def __init__(self, depth=1):
        self.depth = depth
        self.piece_values = {
            PieceType.PAWN: 100,
            PieceType.KNIGHT: 320,
            PieceType.BISHOP: 330,
            PieceType.ROOK: 500,
            PieceType.QUEEN: 900,
            PieceType.KING: 20000,
        }

    def choose_move(self, game):
        """Pick the best move for the current player."""
        color = game.current_player
        moves = list(game.get_all_legal_moves(color))
        if not moves:
            return None

        best_move = moves[0]
        best_score = self.score_move(game, best_move)

        for move in moves[1:]:
            score = self.score_move(game, move)
            if color == Color.WHITE and score > best_score:
                best_score = score
                best_move = move
            elif color == Color.BLACK and score < best_score:
                best_score = score
                best_move = move

        return best_move

    def score_move(self, game, move):
        """Score one move by making a copy of the game and evaluating it."""
        game_copy = deepcopy(game)
        game_copy.make_move(*move)
        return self.evaluate(game_copy)

    def evaluate(self, game):
        """Return a score for the current board.

        Positive means better for White.
        Negative means better for Black.
        """
        if game.game_over:
            if game.winner == 'WHITE':
                return 100000
            if game.winner == 'BLACK':
                return -100000
            return 0

        score = 0

        for row in range(8):
            for col in range(8):
                piece = game.board.get_piece(row, col)
                if piece is None:
                    continue

                value = self.piece_values[piece.type]
                value += self.position_bonus(piece, row, col)

                if piece.color == Color.WHITE:
                    score += value
                else:
                    score -= value

        white_moves = len(game.get_all_legal_moves(Color.WHITE))
        black_moves = len(game.get_all_legal_moves(Color.BLACK))
        score += (white_moves - black_moves) * 2

        if game.board.is_in_check(Color.WHITE):
            score -= 25
        if game.board.is_in_check(Color.BLACK):
            score += 25

        return score

    def position_bonus(self, piece, row, col):
        """Give a tiny bonus for useful squares."""
        center_distance = abs(3.5 - row) + abs(3.5 - col)

        if piece.type == PieceType.PAWN:
            if piece.color == Color.WHITE:
                return (6 - row) * 3
            return (row - 1) * 3

        if piece.type == PieceType.KNIGHT:
            return int((7 - center_distance) * 4)

        if piece.type == PieceType.BISHOP:
            return int((7 - center_distance) * 2)

        if piece.type == PieceType.ROOK:
            return int((7 - center_distance) * 1)

        if piece.type == PieceType.QUEEN:
            return int((7 - center_distance) * 1)

        if piece.type == PieceType.KING:
            return int(-center_distance * 2)

        return 0