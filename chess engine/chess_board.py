"""
Chess board representation and piece logic
"""
from enum import Enum
from typing import Optional, List, Tuple, Set

class Color(Enum):
    WHITE = 1
    BLACK = 2

class PieceType(Enum):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

class Piece:
    def __init__(self, piece_type: PieceType, color: Color):
        self.type = piece_type
        self.color = color
        self.move_count = 0  # Track moves for castling and pawn first move
    
    def __repr__(self):
        white_symbols = {
            PieceType.PAWN: '♙',
            PieceType.KNIGHT: '♘',
            PieceType.BISHOP: '♗',
            PieceType.ROOK: '♖',
            PieceType.QUEEN: '♕',
            PieceType.KING: '♔'
        }
        black_symbols = {
            PieceType.PAWN: '♟',
            PieceType.KNIGHT: '♞',
            PieceType.BISHOP: '♝',
            PieceType.ROOK: '♜',
            PieceType.QUEEN: '♛',
            PieceType.KING: '♚'
        }
        return white_symbols[self.type] if self.color == Color.WHITE else black_symbols[self.type]
    
    def to_dict(self):
        return {
            'type': self.type.name,
            'color': self.color.name,
            'move_count': self.move_count,
            'symbol': str(self)
        }

class ChessBoard:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.setup_initial_position()
        self.white_king_pos = (7, 4)
        self.black_king_pos = (0, 4)
        self.move_history = []
        self.captured_pieces = {'WHITE': [], 'BLACK': []}
        self.en_passant_target = None
    
    def setup_initial_position(self):
        """Set up the standard chess starting position"""
        # Black pieces (top)
        self.board[0][0] = Piece(PieceType.ROOK, Color.BLACK)
        self.board[0][1] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[0][2] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[0][3] = Piece(PieceType.QUEEN, Color.BLACK)
        self.board[0][4] = Piece(PieceType.KING, Color.BLACK)
        self.board[0][5] = Piece(PieceType.BISHOP, Color.BLACK)
        self.board[0][6] = Piece(PieceType.KNIGHT, Color.BLACK)
        self.board[0][7] = Piece(PieceType.ROOK, Color.BLACK)
        
        for i in range(8):
            self.board[1][i] = Piece(PieceType.PAWN, Color.BLACK)
        
        # White pieces (bottom)
        for i in range(8):
            self.board[6][i] = Piece(PieceType.PAWN, Color.WHITE)
        
        self.board[7][0] = Piece(PieceType.ROOK, Color.WHITE)
        self.board[7][1] = Piece(PieceType.KNIGHT, Color.WHITE)
        self.board[7][2] = Piece(PieceType.BISHOP, Color.WHITE)
        self.board[7][3] = Piece(PieceType.QUEEN, Color.WHITE)
        self.board[7][4] = Piece(PieceType.KING, Color.WHITE)
        self.board[7][5] = Piece(PieceType.BISHOP, Color.WHITE)
        self.board[7][6] = Piece(PieceType.KNIGHT, Color.WHITE)
        self.board[7][7] = Piece(PieceType.ROOK, Color.WHITE)
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within board bounds"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Get piece at position"""
        if self.is_valid_position(row, col):
            return self.board[row][col]
        return None
    
    def set_piece(self, row: int, col: int, piece: Optional[Piece]):
        """Set piece at position"""
        if self.is_valid_position(row, col):
            self.board[row][col] = piece
    
    def get_legal_moves(self, row: int, col: int, en_passant_target: Optional[Tuple[int, int]] = None) -> Set[Tuple[int, int]]:
        """Get all legal moves for piece at position"""
        piece = self.get_piece(row, col)
        if not piece:
            return set()
        
        if piece.type == PieceType.PAWN:
            return self._get_pawn_moves(row, col, piece, en_passant_target)
        elif piece.type == PieceType.KNIGHT:
            return self._get_knight_moves(row, col, piece)
        elif piece.type == PieceType.BISHOP:
            return self._get_bishop_moves(row, col, piece)
        elif piece.type == PieceType.ROOK:
            return self._get_rook_moves(row, col, piece)
        elif piece.type == PieceType.QUEEN:
            return self._get_queen_moves(row, col, piece)
        elif piece.type == PieceType.KING:
            return self._get_king_moves(row, col, piece)
        
        return set()
    
    def _get_pawn_moves(self, row: int, col: int, piece: Piece, en_passant_target: Optional[Tuple[int, int]] = None) -> Set[Tuple[int, int]]:
        """Get legal moves for pawn"""
        moves = set()
        direction = -1 if piece.color == Color.WHITE else 1
        start_row = 6 if piece.color == Color.WHITE else 1
        
        # Forward move
        next_row = row + direction
        if self.is_valid_position(next_row, col) and not self.get_piece(next_row, col):
            moves.add((next_row, col))
            
            # Double move from starting position
            if row == start_row:
                next_next_row = row + 2 * direction
                if self.is_valid_position(next_next_row, col) and not self.get_piece(next_next_row, col):
                    moves.add((next_next_row, col))
        
        # Captures (diagonals)
        for dc in [-1, 1]:
            next_row = row + direction
            next_col = col + dc
            if self.is_valid_position(next_row, next_col):
                target = self.get_piece(next_row, next_col)
                if target and target.color != piece.color:
                    moves.add((next_row, next_col))
                elif en_passant_target == (next_row, next_col):
                    moves.add((next_row, next_col))
        
        return moves
    
    def _get_knight_moves(self, row: int, col: int, piece: Piece) -> Set[Tuple[int, int]]:
        """Get legal moves for knight"""
        moves = set()
        knight_moves = [
            (-2, -1), (-2, 1), (-1, -2), (-1, 2),
            (1, -2), (1, 2), (2, -1), (2, 1)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.get_piece(new_row, new_col)
                if not target or target.color != piece.color:
                    moves.add((new_row, new_col))
        
        return moves
    
    def _get_sliding_moves(self, row: int, col: int, piece: Piece, directions: List[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Get moves for sliding pieces (bishop, rook, queen)"""
        moves = set()
        
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while self.is_valid_position(r, c):
                target = self.get_piece(r, c)
                if not target:
                    moves.add((r, c))
                elif target.color != piece.color:
                    moves.add((r, c))
                    break
                else:
                    break
                r, c = r + dr, c + dc
        
        return moves
    
    def _get_bishop_moves(self, row: int, col: int, piece: Piece) -> Set[Tuple[int, int]]:
        """Get legal moves for bishop"""
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        return self._get_sliding_moves(row, col, piece, directions)
    
    def _get_rook_moves(self, row: int, col: int, piece: Piece) -> Set[Tuple[int, int]]:
        """Get legal moves for rook"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return self._get_sliding_moves(row, col, piece, directions)
    
    def _get_queen_moves(self, row: int, col: int, piece: Piece) -> Set[Tuple[int, int]]:
        """Get legal moves for queen"""
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        return self._get_sliding_moves(row, col, piece, directions)
    
    def _get_king_moves(self, row: int, col: int, piece: Piece) -> Set[Tuple[int, int]]:
        """Get legal moves for king"""
        moves = set()
        king_moves = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1)
        ]
        
        for dr, dc in king_moves:
            new_row, new_col = row + dr, col + dc
            if self.is_valid_position(new_row, new_col):
                target = self.get_piece(new_row, new_col)
                if not target or target.color != piece.color:
                    moves.add((new_row, new_col))
        
        return moves
    
    def is_under_attack(self, row: int, col: int, by_color: Color) -> bool:
        """Check if square is under attack by given color"""
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece and piece.color == by_color:
                    moves = self.get_legal_moves(r, c)
                    if (row, col) in moves:
                        return True
        return False
    
    def find_king(self, color: Color) -> Optional[Tuple[int, int]]:
        """Find king position"""
        for r in range(8):
            for c in range(8):
                piece = self.get_piece(r, c)
                if piece and piece.type == PieceType.KING and piece.color == color:
                    return (r, c)
        return None
    
    def is_in_check(self, color: Color) -> bool:
        """Check if player is in check"""
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        return self.is_under_attack(king_pos[0], king_pos[1], enemy_color)
    
    def make_move(self, from_row: int, from_col: int, to_row: int, to_col: int, en_passant_capture: Optional[Tuple[int, int]] = None, promote_to: PieceType = PieceType.QUEEN) -> bool:
        """Make a move on the board"""
        piece = self.get_piece(from_row, from_col)
        if not piece:
            return False
        
        target = self.get_piece(to_row, to_col)
        captured_piece = target
        if en_passant_capture:
            captured_piece = self.get_piece(en_passant_capture[0], en_passant_capture[1])
        
        # Make the move
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)

        if en_passant_capture:
            self.set_piece(en_passant_capture[0], en_passant_capture[1], None)

        piece.move_count += 1

        # Pawn promotion defaults to queen
        promoted_to = None
        if piece.type == PieceType.PAWN and (to_row == 0 or to_row == 7):
            promoted_to = promote_to
            promoted_piece = Piece(promote_to, piece.color)
            promoted_piece.move_count = piece.move_count
            self.set_piece(to_row, to_col, promoted_piece)
            piece = promoted_piece
        
        # Record captured piece
        if captured_piece:
            color_name = 'WHITE' if captured_piece.color == Color.WHITE else 'BLACK'
            self.captured_pieces[color_name].append(str(captured_piece))
        
        # Update king position
        if piece.type == PieceType.KING:
            if piece.color == Color.WHITE:
                self.white_king_pos = (to_row, to_col)
            else:
                self.black_king_pos = (to_row, to_col)
        
        # Record move
        self.move_history.append({
            'from': (from_row, from_col),
            'to': (to_row, to_col),
            'piece': str(piece),
            'captured': str(captured_piece) if captured_piece else None,
            'en_passant_capture': en_passant_capture,
            'promotion': str(promoted_to.name) if promoted_to else None
        })
        
        return True
    
    def to_dict(self) -> dict:
        """Convert board to dictionary for JSON serialization"""
        board_data = []
        for row in self.board:
            row_data = []
            for piece in row:
                if piece:
                    row_data.append(piece.to_dict())
                else:
                    row_data.append(None)
            board_data.append(row_data)
        
        return {
            'board': board_data,
            'white_king_pos': self.white_king_pos,
            'black_king_pos': self.black_king_pos,
            'captured_pieces': self.captured_pieces,
            'move_history': self.move_history
        }
    
    def print_board(self):
        """Print board to console"""
        print("\n   a b c d e f g h")
        for i in range(8):
            print(f"{8-i}  ", end="")
            for j in range(8):
                piece = self.get_piece(i, j)
                print(f"{str(piece) if piece else '.'} ", end="")
            print(f" {8-i}")
        print("   a b c d e f g h\n")
