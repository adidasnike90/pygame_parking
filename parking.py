import os
import pygame
import math
from math import tan, radians, degrees, copysign
from pygame.math import Vector2

black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
grey = (160, 160, 160)
orange = (255, 127, 0)
green = (0, 255, 0)

	
class Car:
	def __init__(self, x, y, angle=0.0, length=4, max_steering=30, max_acceleration=5.0):
		self.position = Vector2(x, y)
		self.velocity = Vector2(0.0, 0.0)
		self.angle = angle
		self.length = length
		self.max_acceleration = max_acceleration
		self.max_steering = max_steering
		self.max_velocity = 20
		self.brake_deceleration = 10
		self.free_deceleration = 2

		self.acceleration = 0.0
		self.steering = 0.0

	def update(self, dt):
		self.velocity += (self.acceleration * dt, 0)
		self.velocity.x = max(-self.max_velocity, min(self.velocity.x, self.max_velocity))

		if self.steering:
			turning_radius = self.length / tan(radians(self.steering))
			angular_velocity = self.velocity.x / turning_radius
		else:
			angular_velocity = 0

		self.position += self.velocity.rotate(-self.angle) * dt
		self.angle += degrees(angular_velocity) * dt

class Lot:
	def __init__(self, x, y, w, l, is_occupied):
		self.x = x
		self.y = y
		self.w = w
		self.l = l
		self.is_occupied = is_occupied
		self.rect = pygame.Rect(self.x, self.y, self.w, self.l)
		self.hitbox = pygame.Rect(self.x - 25, self.y - 25, self.w + 50, self.l + 50)
		
	def render(self, screen):
		pygame.draw.rect(screen, white, self.rect, 10)
		if self.is_occupied:
			pygame.draw.rect(screen, red, self.rect)
		else:
			pygame.draw.rect(screen, green, self.rect)

class Node:
	def __init__(self, pos):
		self.pos = pos
		self.parent = self
		self.g = 0
		self.h = 0
		self.f = 0
		self.neighbors = []

class Game:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Car tutorial")
		self.width = 1280
		self.height = 720
		self.screen = pygame.display.set_mode((self.width, self.height))
		self.clock = pygame.time.Clock()
		self.ticks = 60
		self.exit = False
				
		# parking lots
		self.lots = []
		for i in range(0, 11):
			self.lots.append(Lot(145 + 90 * i, 140, 75, 135, True))
			self.lots.append(Lot(145 + 90 * i, 440, 75, 135, True))
		# set unoccupied lots
		self.lots[11].is_occupied = False
		
	def walkable_space(self):
		step_size = 15
		grid = []
		for y in range(0, self.height, step_size):
			for x in range(0, self.width, step_size):
				b_point = (x, y)
				flag = True
				for o in self.lots:
					if o.hitbox.collidepoint(b_point):
						flag = False
						break
				if flag == True:
					grid.append(b_point)
		return grid
		
	def heuristic(self, point, target):
		return math.sqrt((point[0] - target[0])**2 + (point[1] - target[1])**2)
		
	def get_neighbors(self, node, grid):
		neighbors = []
		if (node.pos[0] + 15, node.pos[1]) in grid:
			neighbors.append(Node((node.pos[0] + 15, node.pos[1])))
		if (node.pos[0] - 15, node.pos[1]) in grid:
			neighbors.append(Node((node.pos[0] - 15, node.pos[1])))
		if (node.pos[0], node.pos[1] + 15) in grid:
			neighbors.append(Node((node.pos[0], node.pos[1] + 15)))
		if (node.pos[0], node.pos[1] - 15) in grid:
			neighbors.append(Node((node.pos[0], node.pos[1] - 15)))
		
		
		return neighbors
				
	def pick_node(self, open_list):
		res = None
		min_f = float("inf")
		for n in open_list:
			if n.f < min_f:
				res = n
				min_f = n.f
		return res
		
	def find_path(self, car_pos, target_pos, grid):
		target_rect = pygame.Rect(target_pos[0], target_pos[1], 30, 30)
		start_pos = car_pos
		min_value = float("inf")
		for g in grid:
			if math.sqrt((car_pos[0] - g[0])**2 + (car_pos[1] - g[1])**2) < min_value:
				min_value = math.sqrt((car_pos[0] - g[0])**2 + (car_pos[1] - g[1])**2)
				start_pos = g
		
		start = Node(start_pos)
		start.f = self.heuristic(start_pos, target_pos)
		close_list = []
		open_list = []
		open_list.append(start)
		
		while len(open_list) != 0:
			q = self.pick_node(open_list)
			open_list.remove(q)
			if target_rect.collidepoint(q.pos):
				close_list.append(Node(target_pos))
				return close_list
			q.neighbors = self.get_neighbors(q, grid)
			for n in q.neighbors:
				cost = q.g + 1
				if n in open_list:
					if n.g <= q.f:
						continue
				elif n in close_list:
					if n.g <= q.f:
						close_list.remove(n)
						open_list.append(n)
						continue
				else:
					open_list.append(n)
					n.h = self.heuristic(n.pos, target_pos)
					n.f = n.g + n.h
				n.g = cost
				n.f = n.g + n.h
				n.parent = q
			close_list.append(q)
		return close_list
		#return [car_pos, (400, 600), (550, 700), target_pos]

	def run(self):
		current_dir = os.path.dirname(os.path.abspath(__file__))
		image_path = os.path.join(current_dir, "car.png")
		car_image = pygame.image.load(image_path)
		car = Car(0, 0)
		ppu = 32
		target = car.position * ppu
		grid = self.walkable_space()
		path = []
			
		while not self.exit:
			dt = self.clock.get_time() / 1000

			# Event queue
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.exit = True

			# User input
			pressed = pygame.key.get_pressed()

			if pressed[pygame.K_UP]:
				if car.velocity.x < 0:
					car.acceleration = car.brake_deceleration
				else:
					car.acceleration += 1 * dt
			elif pressed[pygame.K_DOWN]:
				if car.velocity.x > 0:
					car.acceleration = -car.brake_deceleration
				else:
					car.acceleration -= 1 * dt
			elif pressed[pygame.K_SPACE]:
				if abs(car.velocity.x) > dt * car.brake_deceleration:
					car.acceleration = -copysign(car.brake_deceleration, car.velocity.x)
				else:
					car.acceleration = -car.velocity.x / dt
			else:
				if abs(car.velocity.x) > dt * car.free_deceleration:
					car.acceleration = -copysign(car.free_deceleration, car.velocity.x)
				else:
					if dt != 0:
						car.acceleration = -car.velocity.x / dt
			car.acceleration = max(-car.max_acceleration, min(car.acceleration, car.max_acceleration))

			if pressed[pygame.K_RIGHT]:
				car.steering -= 30 * dt
			elif pressed[pygame.K_LEFT]:
				car.steering += 30 * dt
			else:
				car.steering = 0
			car.steering = max(-car.max_steering, min(car.steering, car.max_steering))
			
			# Logic
			car.update(dt)

			# Drawing
			self.screen.fill(grey)
			
			for l in self.lots:
				l.render(self.screen)
			
			for g in grid:
				pygame.draw.circle(self.screen, green, g, 1, 1)

			
			rotated = pygame.transform.rotate(car_image, car.angle)
			rect = rotated.get_rect()
			self.screen.blit(rotated, car.position * ppu - (rect.width / 2, rect.height / 2))
			
			# Route generation
			clicked = pygame.mouse.get_pressed()
			
			
			if clicked[0]:
				target = pygame.mouse.get_pos()
				path = []
				path = self.find_path(car.position * ppu, target, grid)
				
				
			#pygame.draw.line(self.screen, orange, car.position * ppu, target, 10)
			
			
			for i in range(0, len(path) - 1):
				pygame.draw.line(self.screen, orange, path[i].pos, path[i + 1].pos, 10)
			
			
			pygame.display.flip()
			
			

			self.clock.tick(self.ticks)
		pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
