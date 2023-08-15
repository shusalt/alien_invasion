from time import sleep

import pygame
import sys

from alien import Alien
from bullet import Bullet
from button import Button
from game_stats import GameStats
from scoreboard import Scoreboard
from settings import Settings
from ship import Ship


class AlienInvasion:
    """管理游戏资源和行为的类"""
    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        # 初始化设置对象
        self.settings = Settings()
        self.screen = pygame.display.set_mode((self.settings.screen_width,
                                             self.settings.screen_height))
        # self.screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        # self.settings.screen_width = self.screen.get_rect().width
        # self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")
        # 游戏统计信息实例
        self.stats = GameStats(self)
        # 创建记分牌
        self.sb = Scoreboard(self)
        # ship飞船对象
        self.ship = Ship(self)
        # 子弹编组
        self.bullets = pygame.sprite.Group()
        # 外星人编组
        self.aliens = pygame.sprite.Group()

        self._create_fleet()

        # 创建play按钮
        self.play_button = Button(self, "Play")

    def run_game(self):
        """开始游戏主循环"""
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            self._update_screen()

    def _check_events(self):
        """响应按键和鼠标事件"""
        # 监视鼠标和键盘事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)

            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """在玩家单击play按钮时开始游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # 重置游戏
            self.settings.initialize_dynamic_settings()
            # 重置游戏统计信息
            self.stats.rest_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # 清空剩余的外星人和子弹
            self.aliens.empty()
            self.bullets.empty()

            # 创建一群新的外星人并让飞船居中
            self._create_fleet()
            self.ship.center_ship()

            # 隐藏鼠标光标
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """响应按键"""
        if event.key == pygame.K_RIGHT:
            # 向右移动飞船
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            # 向左移动飞船
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            # 按大写‘Q’键退出
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self, event):
        """响应松开"""
        if event.key == pygame.K_RIGHT:
            # 松开键停止移动
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        """创建一颗子弹，并将其加入编组bullets中"""
        if len(self.bullets) < self.settings.bullet_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """更新子弹的位置并删除消失的子弹"""
        # 更新子弹
        self.bullets.update()
        # 删除消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collections()

    def _check_bullet_alien_collections(self):
        """响应子弹和外星人碰撞"""
        # 检查是否有子弹击中了外星人
        # 如果是，就删除相应的子弹和外星人
        collections = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        # 更新得分
        if collections:
            for aliens in collections.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            # 更新最高得分
            self.sb.check_high_score()


        # 检查外星人群是否被全部消灭，
        # 是：清空现有子弹sprites，重新创建外星人群
        if not self.aliens:
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # 提高等级
            self.stats.level += 1
            self.sb.prep_level()

        if not self.aliens:
            # 删除现有的子弹并创建一群新的外星人
            self.bullets.empty()
            self._create_alien()


    def _create_fleet(self):
        """创建外星人群"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_alien_x = available_space_x // (2 * alien_width)

        # 计算屏幕可容纳多少行外星人
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # 创建外星人群
        for row_number in range(number_rows):
            for alien_number in range(number_alien_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        """创建一个外星人，并将其放在当前行"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + (2 * alien_width * alien_number)
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + (2 * alien.rect.height * row_number)
        self.aliens.add(alien)

    def _update_aliens(self):
        """更新外星人群中所有外星人的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # 检查是否有外星人到达屏幕低端
        self._check_aliens_bottom()

    def _ship_hit(self):
        """响应飞船被外星人撞到，或者外星人触碰到屏幕底部"""

        if self.stats.ships_left > 0:
            # 将ship_left减1
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            # 清空剩余的子弹和外星人
            self.bullets.empty()
            self.aliens.empty()

            # 创建一群新的外星人， 并将飞船放到屏幕低端的中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_fleet_edges(self):
        """有外星人到达边缘时采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """将整个外星人下移，并改变它们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """检查是否有外星人到达了屏幕低端"""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # 像飞船被撞到一样处理
                self._ship_hit()
                break

    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
        # 每次循环时都重绘屏幕
        self.screen.fill(self.settings.bg_color)
        # 将飞船绘制在屏幕上
        self.ship.blitme()
        # 将子弹绘制在屏幕上
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        # 将外星人绘制到屏幕上
        self.aliens.draw(self.screen)
        # 显示得分
        self.sb.show_score()

        # 如果游戏处于非活动状态，就绘制Play按钮
        if not self.stats.game_active:
            self.play_button.draw_button()

        # 让最近绘制的屏幕可见
        pygame.display.flip()

if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()
