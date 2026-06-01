"""
Chess game logic - handles game state, turns, check/checkmate detection
"""
from chess_board import ChessBoard, Color, PieceType
from typing import Optional, List, Tuple, Set

class ChessGame:
    def __init__(self):
        self.board = ChessBoard()
        self.current_player = Color.WHITE
        self.move_count = 0
        self.game_over = False
        self.winner = None  # None, 'WHITE', 'BLACK', or 'STALEMATE'
        self.fifty_move_rule = 0  # Moves without pawn move or capture
        self.threefold_repetition = {}
        self.game_state_history = []
        self.en_passant_target = None
    
    def get_all_legal_moves(self, color: Color) -> Set[Tuple[int, int, int, int]]:
        """Get all legal moves for a color"""
        legal_moves = set()
        
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == color:
                    moves = self.board.get_legal_moves(row, col, self.en_passant_target)
                    for to_row, to_col in moves:
                        # Check if move leaves king in check
                        if self._is_legal_move(row, col, to_row, to_col, color):
                            legal_moves.add((row, col, to_row, to_col))
        
        return legal_moves
    
    def _is_legal_move(self, from_row: int, from_col: int, to_row: int, to_col: int, color: Color) -> bool:
        """Check if move is legal (doesn't leave king in check)"""
        # Save board state
        original_piece = self.board.get_piece(to_row, to_col)
        moved_piece = self.board.get_piece(from_row, from_col)
        en_passant_capture = self._get_en_passant_capture(from_row, from_col, to_row, to_col, moved_piece, original_piece)
        captured_piece = None
        
        # Make move temporarily
        self.board.set_piece(to_row, to_col, moved_piece)
        self.board.set_piece(from_row, from_col, None)

        if en_passant_capture:
            captured_piece = self.board.get_piece(en_passant_capture[0], en_passant_capture[1])
            self.board.set_piece(en_passant_capture[0], en_passant_capture[1], None)
        
        # Update king position temporarily if king moved
        if moved_piece.type == PieceType.KING:
            if color == Color.WHITE:
                self.board.white_king_pos = (to_row, to_col)
            else:
                self.board.black_king_pos = (to_row, to_col)
        
        # Check if in check
        in_check = self.board.is_in_check(color)
        
        # Restore board state
        self.board.set_piece(from_row, from_col, moved_piece)
        self.board.set_piece(to_row, to_col, original_piece)

        if en_passant_capture:
            self.board.set_piece(en_passant_capture[0], en_passant_capture[1], captured_piece)
        
        # Restore king position
        if moved_piece.type == PieceType.KING:
            if color == Color.WHITE:
                self.board.white_king_pos = (from_row, from_col)
            else:
                self.board.black_king_pos = (from_row, from_col)
        
        return not in_check
    
    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Make a move and update game state"""
        if self.game_over:
            return False
        
        piece = self.board.get_piece(from_row, from_col)
        if not piece or piece.color != self.current_player:
            return False

        en_passant_capture = self._get_en_passant_capture(from_row, from_col, to_row, to_col, piece, self.board.get_piece(to_row, to_col))
        
        # Check if move is legal
        if not self._is_legal_move(from_row, from_col, to_row, to_col, self.current_player):
            return False
        
        # Check if move is in available moves
        legal_moves = self.board.get_legal_moves(from_row, from_col, self.en_passant_target)
        if (to_row, to_col) not in legal_moves:
            return False
        
        # Make the move
        target = self.board.get_piece(to_row, to_col)
        captured_piece = target
        if en_passant_capture:
            captured_piece = self.board.get_piece(en_passant_capture[0], en_passant_capture[1])

        if piece.type == PieceType.PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, from_col)
        else:
            self.en_passant_target = None

        self.board.en_passant_target = self.en_passant_target
        self.board.make_move(from_row, from_col, to_row, to_col, en_passant_capture=en_passant_capture)
        
        # Update fifty move rule
        if piece.type == PieceType.PAWN or captured_piece:
            self.fifty_move_rule = 0
        else:
            self.fifty_move_rule += 1
        
        # Save game state for threefold repetition
        state = self._get_board_state()
        self.threefold_repetition[state] = self.threefold_repetition.get(state, 0) + 1
        
        self.move_count += 1
        self._switch_player()
        self._check_game_end()
        
        return True
    
    def _switch_player(self):
        """Switch current player"""
        self.current_player = Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
    
    def _get_board_state(self) -> str:
        """Get current board state as string for repetition detection"""
        state = ""
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece:
                    state += str(piece)
                else:
                    state += "."
        return state

    def _get_en_passant_capture(self, from_row: int, from_col: int, to_row: int, to_col: int, piece, target) -> Optional[Tuple[int, int]]:
        """Return the captured pawn square for an en passant move, if any."""
        if not piece or piece.type != PieceType.PAWN:
            return None
        if target is not None:
            return None
        if self.en_passant_target != (to_row, to_col):
            return None
        if abs(to_col - from_col) != 1:
            return None
        direction = -1 if piece.color == Color.WHITE else 1
        if to_row != from_row + direction:
            return None
        return (from_row, to_col)
    
    def _check_game_end(self):
        """Check if game has ended"""
        legal_moves = self.get_all_legal_moves(self.current_player)
        
        if not legal_moves:
            # No legal moves - check or stalemate
            if self.board.is_in_check(self.current_player):
                # Checkmate
                self.game_over = True
                opponent = Color.WHITE if self.current_player == Color.BLACK else Color.BLACK
                self.winner = 'WHITE' if opponent == Color.WHITE else 'BLACK'
            else:
                # Stalemate
                self.game_over = True
                self.winner = 'STALEMATE'
        elif self.fifty_move_rule >= 100:
            # Fifty move rule (100 half-moves)
            self.game_over = True
            self.winner = 'STALEMATE'
        elif max(self.threefold_repetition.values()) >= 3:
            # Threefold repetition
            self.game_over = True
            self.winner = 'STALEMATE'
    
    def get_game_status(self) -> dict:
        """Get current game status"""
        return {
            'current_player': self.current_player.name,
            'move_count': self.move_count,
            'game_over': self.game_over,
            'winner': self.winner,
            'white_in_check': self.board.is_in_check(Color.WHITE),
            'black_in_check': self.board.is_in_check(Color.BLACK),
            'en_passant_target': self.en_passant_target,
            'board': self.board.to_dict()
        }
    
    def is_move_valid(self, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Check if move is valid"""
        piece = self.board.get_piece(from_row, from_col)
        if not piece or piece.color != self.current_player:
            return False
        
        legal_moves = self.board.get_legal_moves(from_row, from_col, self.en_passant_target)
        if (to_row, to_col) not in legal_moves:
            return False
        
        return self._is_legal_move(from_row, from_col, to_row, to_col, self.current_player)
    
    def reset_game(self):
        """Reset game to initial state"""
        self.__init__()
    
    def get_board_as_list(self) -> List[List[dict]]:
        """Get board representation as list for frontend"""
        board_list = []
        for row in range(8):
            row_list = []
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece:
                    row_list.append({
                        'type': piece.type.name,
                        'color': piece.color.name
                    })
                else:
                    row_list.append(None)
            board_list.append(row_list)
        return board_list
