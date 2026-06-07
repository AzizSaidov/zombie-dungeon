# Точка входа в игру Dead Crawler
import pygame
from src.core.game import Game


def main():
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
