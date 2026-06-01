// Chess Game Frontend
class ChessUI {
    constructor() {
        this.selectedSquare = null;
        this.availableMoves = [];
        this.gameState = null;
        this.board = null;
        this.initializeBoard();
        this.loadGameState();
    }

    initializeBoard() {
        const boardElement = document.getElementById('board');
        boardElement.innerHTML = '';
        
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.createElement('div');
                square.className = 'square';
                square.id = `square-${row}-${col}`;
                
                // Alternate colors
                if ((row + col) % 2 === 0) {
                    square.classList.add('light');
                } else {
                    square.classList.add('dark');
                }
                
                square.addEventListener('click', () => this.handleSquareClick(row, col));
                boardElement.appendChild(square);
            }
        }
    }

    async loadGameState() {
        try {
            const response = await fetch('/api/game/status');
            this.gameState = await response.json();
            this.board = this.gameState.board.board;
            this.renderBoard();
            this.updateStatus();
        } catch (error) {
            console.error('Error loading game state:', error);
        }
    }

    renderBoard() {
        // Clear all pieces
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const square = document.getElementById(`square-${row}-${col}`);
                square.textContent = '';
            }
        }

        // Place pieces
        for (let row = 0; row < 8; row++) {
            for (let col = 0; col < 8; col++) {
                const piece = this.board[row][col];
                if (piece) {
                    const square = document.getElementById(`square-${row}-${col}`);
                    square.textContent = this.getPieceSymbol(piece.type, piece.color);
                }
            }
        }

        // Highlight checks
        if (this.gameState.white_in_check) {
            const [kingRow, kingCol] = this.gameState.board.white_king_pos;
            document.getElementById(`square-${kingRow}-${kingCol}`).classList.add('in-check');
        }
        if (this.gameState.black_in_check) {
            const [kingRow, kingCol] = this.gameState.board.black_king_pos;
            document.getElementById(`square-${kingRow}-${kingCol}`).classList.add('in-check');
        }
    }

    getPieceSymbol(type, color) {
        const whiteSymbols = {
            PAWN: '♙',
            KNIGHT: '♘',
            BISHOP: '♗',
            ROOK: '♖',
            QUEEN: '♕',
            KING: '♔'
        };
        const blackSymbols = {
            PAWN: '♟',
            KNIGHT: '♞',
            BISHOP: '♝',
            ROOK: '♜',
            QUEEN: '♛',
            KING: '♚'
        };

        return color === 'WHITE' ? whiteSymbols[type] : blackSymbols[type];
    }

    async handleSquareClick(row, col) {
        const square = document.getElementById(`square-${row}-${col}`);
        const piece = this.board[row][col];

        // If clicking on selected square, deselect
        if (this.selectedSquare && this.selectedSquare[0] === row && this.selectedSquare[1] === col) {
            this.deselectSquare();
            return;
        }

        // If a square is already selected, try to move
        if (this.selectedSquare) {
            const [fromRow, fromCol] = this.selectedSquare;
            
            // If clicking on same color piece, select that instead
            if (piece && piece.color === this.gameState.current_player) {
                this.deselectSquare();
                await this.selectSquare(row, col);
                return;
            }

            // Try to move
            await this.makeMove(fromRow, fromCol, row, col);
            this.deselectSquare();
        } else {
            // Select piece if it's the current player's piece
            if (piece && piece.color === this.gameState.current_player) {
                await this.selectSquare(row, col);
            }
        }
    }

    async selectSquare(row, col) {
        const square = document.getElementById(`square-${row}-${col}`);
        const piece = this.board[row][col];

        if (!piece || piece.color !== this.gameState.current_player) {
            return;
        }

        this.selectedSquare = [row, col];
        square.classList.add('selected');

        // Load available moves
        try {
            const response = await fetch('/api/game/moves', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ row, col })
            });
            
            const data = await response.json();
            this.availableMoves = data.moves;

            // Highlight available moves
            for (const move of this.availableMoves) {
                const moveSquare = document.getElementById(`square-${move.row}-${move.col}`);
                const targetPiece = this.board[move.row][move.col];
                
                if (move.capture || targetPiece) {
                    moveSquare.classList.add('capture');
                } else {
                    moveSquare.classList.add('available');
                }
            }
        } catch (error) {
            console.error('Error loading moves:', error);
        }
    }

    deselectSquare() {
        if (this.selectedSquare) {
            const [row, col] = this.selectedSquare;
            const square = document.getElementById(`square-${row}-${col}`);
            square.classList.remove('selected');
        }

        // Remove highlights
        for (const move of this.availableMoves) {
            const moveSquare = document.getElementById(`square-${move.row}-${move.col}`);
            moveSquare.classList.remove('available', 'capture');
        }

        this.selectedSquare = null;
        this.availableMoves = [];
    }

    async makeMove(fromRow, fromCol, toRow, toCol) {
        try {
            const response = await fetch('/api/game/move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    from_row: fromRow,
                    from_col: fromCol,
                    to_row: toRow,
                    to_col: toCol
                })
            });

            const data = await response.json();

            if (data.success) {
                this.gameState = data.game_status;
                this.board = this.gameState.board.board;
                this.renderBoard();
                this.updateStatus();

                if (!this.gameState.game_over && this.gameState.current_player === 'BLACK') {
                    await this.playEngineMove();
                }
            } else {
                alert('Invalid move: ' + data.error);
            }
        } catch (error) {
            console.error('Error making move:', error);
            alert('Error making move');
        }
    }

    updateStatus() {
        const currentPlayerElement = document.getElementById('current-player');
        const gameStatusElement = document.getElementById('game-status');

        const playerName = this.gameState.current_player === 'WHITE' ? 'White' : 'Black';
        currentPlayerElement.textContent = playerName;

        let statusText = 'In Progress';
        if (this.gameState.white_in_check) {
            statusText = 'White is in Check';
        } else if (this.gameState.black_in_check) {
            statusText = 'Black is in Check';
        }

        if (this.gameState.game_over) {
            if (this.gameState.winner === 'WHITE') {
                statusText = 'White Wins!';
            } else if (this.gameState.winner === 'BLACK') {
                statusText = 'Black Wins!';
            } else {
                statusText = 'Game Over - Stalemate';
            }
        }

        gameStatusElement.textContent = statusText;
    }

    async playEngineMove() {
        try {
            const response = await fetch('/api/game/engine-move', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            if (data.success) {
                this.gameState = data.game_status;
                this.board = this.gameState.board.board;
                this.renderBoard();
                this.updateStatus();
            }
        } catch (error) {
            console.error('Error making engine move:', error);
        }
    }
}

async function resetGame() {
    try {
        const response = await fetch('/api/game/reset', {
            method: 'POST'
        });
        
        if (response.ok) {
            // Reload the game
            ui.loadGameState();
        }
    } catch (error) {
        console.error('Error resetting game:', error);
    }
}

// Initialize the UI when page loads
let ui;
document.addEventListener('DOMContentLoaded', () => {
    ui = new ChessUI();
});
