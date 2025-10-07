import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
NUM_OF_BOMBS = 5
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """オブジェクトが画面内or画面外を判定"""
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """こうかとん"""
    delta = {
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)
    imgs = {
        (+5, 0): img,
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),
        (-5, 0): img0,
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if sum_mv != [0, 0]:
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Beam:
    """ビーム"""
    def __init__(self, bird: "Bird"):
        self.img = pg.image.load("fig/beam.png")
        self.rct = self.img.get_rect()
        self.rct.centery = bird.rct.centery
        self.rct.left = bird.rct.right
        self.vx, self.vy = +5, 0

    def update(self, screen: pg.Surface):
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Bomb:
    """爆弾"""
    def __init__(self, color: tuple[int, int, int], rad: int):
        self.img = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = +5, +5

    def update(self, screen: pg.Surface):
        yoko, tate = check_bound(self.rct)
        if not yoko: self.vx *= -1
        if not tate: self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)


class Score:
    """スコア"""
    def __init__(self):
        self.fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 30)
        self.color = (0, 0, 255)
        self.value = 0
        self.img = self.fonto.render(f"スコア：{self.value}", True, self.color)
        self.rct = self.img.get_rect()
        self.rct.center = (100, HEIGHT - 50)

    def add(self, n: int = 1):
        self.value += n

    def update(self, screen: pg.Surface):
        self.img = self.fonto.render(f"スコア：{self.value}", True, self.color)
        screen.blit(self.img, self.rct)


class Explosion:
    """爆発エフェクト"""
    def __init__(self, center: tuple[int, int]):
        img0 = pg.image.load("fig/explosion.gif")  # 元画像
        img1 = pg.transform.flip(img0, True, True)  # 上下左右反転
        self.imgs = [img0, img1]  # 2枚の爆発画像
        self.life = 30  # 爆発が表示されるフレーム数
        self.rct = self.imgs[0].get_rect()
        self.rct.center = center  # 爆発中心位置

    def update(self, screen: pg.Surface):
        self.life -= 1
        if self.life > 0:
            img = self.imgs[self.life % 2]  # 交互に切替
            screen.blit(img, self.rct)


def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")

    bird = Bird((300, 200))
    bombs = [Bomb((255, 0, 0), 10) for _ in range(NUM_OF_BOMBS)]
    beams: list[Beam] = []
    explosions: list[Explosion] = []  # ★爆発リスト
    score = Score()

    clock = pg.time.Clock()
    tmr = 0

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.append(Beam(bird))

        screen.blit(bg_img, [0, 0])

        # --- 衝突処理 ---
        for i, bomb in enumerate(bombs):
            # こうかとんが爆弾に当たったらゲームオーバー
            if bird.rct.colliderect(bomb.rct):
                bird.change_img(8, screen)
                fonto = pg.font.Font(None, 80)
                txt = fonto.render("Game Over", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2 - 150, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

            # ビームと爆弾の衝突判定
            for j, beam in enumerate(beams):
                if beam is not None and beam.rct.colliderect(bomb.rct):
                    bombs[i] = None
                    beams[j] = None
                    score.add(1)
                    explosions.append(Explosion(bomb.rct.center))  # ★爆発発生

        # リスト更新（None削除 & 画面外ビーム削除）
        bombs = [b for b in bombs if b is not None]
        beams = [b for b in beams if b is not None and check_bound(b.rct)[0]]
        explosions = [ex for ex in explosions if ex.life > 0]  # ★生き残り爆発だけ残す

        # --- 描画 ---
        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for beam in beams:
            beam.update(screen)
        for bomb in bombs:
            bomb.update(screen)
        for ex in explosions:  # ★爆発を描画
            ex.update(screen)
        score.update(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
