# Zombie Dungeon

2D roguelike dungeon crawler на Python + Pygame.

Убивай зомби, собирай лут, исследуй процедурно генерируемые комнаты. Каждый запуск — новая карта.

## Стек

- Python 3.12
- Pygame 2.6.1

## Запуск

```bash
# Активировать виртуальное окружение
.venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt

# Запустить игру
python main.py
```

## Структура проекта

```
zombie-dungeon/
├── main.py              # Точка входа
├── requirements.txt
├── assets/              # Картинки, звуки, шрифты
└── src/
    ├── core/            # Game loop, настройки, камера
    ├── entities/        # Игрок, зомби, пули, лут
    ├── rooms/           # Генерация комнат и карты
    └── ui/              # HUD, меню, game over экран
```

## Жанр

Вдохновение: Binding of Isaac, Enter the Gungeon (упрощённая версия).
