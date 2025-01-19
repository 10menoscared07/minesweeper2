import pygame, sys, random, math
pygame.init()

vec2 = pygame.math.Vector2

def near(x, y):
    if  abs(x-y) <= 0.005:
        return True 
    return False

def scaleUp(img, scale=1):
    w,h = img.get_size()
    return pygame.transform.scale(img, (w*scale, h*scale)).convert_alpha()

def loadImage(path, scale=1):
    img = pygame.image.load(path).convert_alpha()
    return scaleUp(img, scale)

def clamp(val, mini, maxi):
    if val >= maxi:
        return maxi
    if val <= mini:
        return mini
    return val

def palette_swap(surf, old_c, new_c):
    img_copy = pygame.Surface(surf.get_size())
    img_copy.fill(new_c)
    surf.set_colorkey(old_c)
    img_copy.blit(surf, (0, 0))
    return img_copy


def distance(v1, v2):
    return math.sqrt(math.pow(v2.x - v1.x, 2) + math.pow(v2.y - v1.y, 2))

### required classes
class Timer:
    def __init__(self, duration):
        self.duration = duration
        self.timer = 0
        self.finsied = False
    
    def update(self, deltaTime):
        self.timer += deltaTime
        if self.timer >= self.duration:
            self.finsied = True

    def percentCompleted(self):
        return clamp(self.timer/self.duration, 0, 1)

    def isOver(self):
        return self.finsied
    
    def end(self):
        self.timer = 0
        self.finsied = True

    def reset(self):
        self.timer = 0
        self.finsied = False

class Cell:
    def __init__(self, pos, size, typeC="none"):
        self.pos = pos + size/2
        self.size = size
        self.type = typeC

        self.rect = pygame.Rect(0, 0, size.x, size.y)
        self.rect.center = self.pos


        self.flagged = False  ### flaggign as done in the original game
        self.flagAnim = False
        self.flagAnimTimer = Timer(0.2)
        self.flagAnimRect = self.rect.copy()


        self.thick = vec2(5, 5)
        self.currentThick = vec2(0,0)
        self.outlineRect = pygame.Rect(0,0, size.x + self.currentThick.x, size.y + self.currentThick.y)
        self.outlineRect.center = self.pos

        self.isHovered = False

        ### revealing animtion
        self.isRevealed = False

        self.revealInAnimating = False    
        self.revealInTime = 0.1
        self.revealInTimer = Timer(self.revealInTime)
        self.revealInRect = pygame.Rect(0,0,0,0)
        
        self.revealOutTime = 0.5
        self.revealOutTimer = Timer(self.revealOutTime)
        self.revealOutAnimating = False
        self.revealOutRect = self.rect.copy()


        self.revealBegin = False
        self.revealDelayTimer = None
        self.goingToBeRevealed = False

        self.revealColor = (21, 96, 100)
        self.flagColor = (155, 41, 21)
        self.bg = (32, 27, 34)
        self.hoverColor = (246, 174, 45)
        self.outlineColor = (200,200,200)

        self.value = 0
        self.image = None
        self.imageRect = None

        self.popSfx = pygame.mixer.Sound("assets/pop.ogg")
        self.popSfx.set_volume(0.8)
        # self.popSfx.fadeout()
        self.sfxPlayed = False

    def setHoverImage(self, hoverImage):
        self.hoverImage = hoverImage
        self.hoverRect = self.hoverImage.get_rect(center=self.pos)

    def setFlagImage(self, flagImage, outlineColor):
        self.flagImage = flagImage
        self.flagRect = self.flagImage.get_rect(center=self.pos)
        self.rectOutlineColor = outlineColor

    def flagit(self):
        ### if flagged -> unflag it and if not flagged -> flag it
        self.flagAnim = True

    def setValue(self, value, image):
        self.value = value
        self.image = image
        self.imageRect = self.image.get_rect(center=self.pos)

    def reveal(self, time=1):
        self.revealDelayTimer = Timer(time - (self.revealOutTime + self.revealInTime))
        self.revealBegin = True
        self.goingToBeRevealed = True

    def update(self, dt=1/60, offset=vec2(0,0)):
        mousePos = vec2(*pygame.mouse.get_pos()) - offset

        ### check if the cell is hovered
        self.isHovered = False
        if self.rect.collidepoint(mousePos):
            self.isHovered = True

        ### reveal animtion handler

        if self.revealBegin:
            self.revealDelayTimer.update(dt)

            if self.revealDelayTimer.isOver():
                self.revealInAnimating = True
                self.revealBegin = False

        if self.revealInAnimating:
            self.revealInTimer.update(dt)

            factor = self.revealInTimer.percentCompleted()

            self.revealInRect.width = self.rect.width * factor
            self.revealInRect.height = self.rect.height * factor
            self.revealInRect.center = self.rect.center

            if self.revealInTimer.isOver():
                self.revealOutAnimating = True
                self.revealInAnimating = False
                self.flagged = False
                self.isRevealed = True

        if self.revealOutAnimating:
            self.revealOutTimer.update(dt)

            factor = self.revealOutTimer.percentCompleted()
            invfactor = 1- factor
            

            self.revealOutRect.width = self.rect.width * invfactor
            self.revealOutRect.height = self.rect.height * invfactor
            self.revealOutRect.center = self.rect.center

            self.currentThick.x = self.thick.x * factor
            self.currentThick.y = self.thick.y * factor
            self.outlineRect = pygame.Rect(0,0, self.size.x + self.currentThick.x, self.size.y + self.currentThick.y)
            self.outlineRect.center = self.pos

            if self.revealOutTimer.percentCompleted() >= .35 and not self.sfxPlayed:
                self.sfxPlayed = True
                self.popSfx.play()
                
            if self.revealOutTimer.isOver():
                self.revealOutAnimating = False
                self.isRevealed = True
                # self.popSfx.play()


        if self.flagAnim:
            self.flagAnimTimer.update(dt)

            factor = self.flagAnimTimer.percentCompleted()
            invFactor = 1 - factor
            
            ### if cell was flagged previously
            if not self.flagged:
                self.flagAnimRect.height = self.rect.height * invFactor
                self.flagAnimRect.bottom = self.rect.bottom

                self.currentThick.x = self.thick.x * factor
                self.currentThick.y = self.thick.y * factor
                self.outlineRect = pygame.Rect(0,0, self.size.x + self.currentThick.x, self.size.y + self.currentThick.y)
                self.outlineRect.center = self.pos


            if self.flagged:
                self.flagAnimRect.height = self.rect.height * factor
                self.flagAnimRect.bottom = self.rect.bottom


                self.currentThick.x = self.thick.x * invFactor
                self.currentThick.y = self.thick.y * invFactor
                self.outlineRect = pygame.Rect(0,0, self.size.x + self.currentThick.x, self.size.y + self.currentThick.y)
                self.outlineRect.center = self.pos


            if self.flagAnimTimer.isOver():
                self.flagAnim = False
                self.flagAnimTimer.reset()
                self.flagged = not self.flagged

    def drawOutline(self, window):
        if self.isRevealed or self.revealOutAnimating:
            pygame.draw.rect(window, self.outlineColor, self.outlineRect)
        
        elif self.flagAnim or self.flagged:
            pygame.draw.rect(window, self.outlineColor, self.outlineRect)

    def draw(self, window):
        if self.isRevealed:
            pygame.draw.rect(window, self.bg, self.rect)
            if self.image:
                window.blit(self.image, self.imageRect)

        if self.revealInAnimating:
            pygame.draw.rect(window,  self.revealColor, self.revealInRect)
            pygame.draw.rect(window,  self.rectOutlineColor, self.revealInRect, 2)


        if self.revealOutAnimating:
            pygame.draw.rect(window,  self.revealColor, self.revealOutRect)
            pygame.draw.rect(window,  self.rectOutlineColor, self.revealOutRect, 2)


        ### draws flag if the cell is flagged
        if self.flagged:
            pygame.draw.rect(window, self.bg, self.rect)
            window.blit(self.flagImage, self.flagRect)

        ### if the flag animation is going on
        if self.flagAnim:
            pygame.draw.rect(window, self.bg, self.rect)
            window.blit(self.flagImage, self.flagRect)
            pygame.draw.rect(window, self.bg, self.flagAnimRect)
            pygame.draw.rect(window, self.rectOutlineColor, self.flagAnimRect, 2)

        ### renders if the cell is hovered
        if self.isHovered:
            window.blit(self.hoverImage, self.hoverRect)

class SineAnimation:
    def __init__(self, extreme, duration, base=0, nonNegative=False, nonPositive=False, variable=False, secondHalf=0.5):
        self.PI = 3.141
        self.base = base
        self.firstHaldExtreme = extreme
        self.duration = duration
        self.nonNegative = nonNegative
        self.nonPositive = nonPositive
        self.variable = variable
        self.secondHalfExtreme = secondHalf

        self.extreme = self.firstHaldExtreme

        self.speed = 2*self.PI/self.duration

        self.angle = 0

        self.value = 0
        self.counter = 0

        self.over = False

    def update(self, deltaTime):
        if not self.over:
            self.angle += self.speed * deltaTime

            if self.nonNegative:
                self.value = self.base + (abs(math.sin(self.angle))) * self.extreme
                # print(self.base)
            elif self.nonPositive:
                self.value = self.base - abs(math.sin(self.angle)) * self.extreme
            else:
                self.value = self.base + math.sin(self.angle) * self.extreme

            # if math.sin(self.angle) == 0:d

            if self.angle >= self.PI:
                if self.variable:
                    self.extreme = self.secondHalfExtreme
            else:
                self.extreme = self.firstHaldExtreme

            if self.angle >= self.PI*2:
                self.over = True
                self.angle = 0

    def restart(self):
        self.angle = 0
        self.over = False


    def continueRunning(self):
        self.over = False

    def getValue(self):
        return self.value

    def isOver(self):
        return self.over

class PatternBg:
    def __init__(self, resolution=vec2(600,600), scale=1):
        self.resolution = resolution
        self.scale = scale

        self.patternid = "assets/pattern.png"

        self.tileImage = loadImage(self.patternid, self.scale)

        self.displace = vec2(0,0)
        self.velocity = vec2(0,0)
        self.offsetTile = vec2(-2, -2)
        self.buffer = 3
        
        self.decoySurf = None

        self.adaptChanges()    
        
    def setVelocity(self, vel:vec2) -> None:
        self.velocity = vel

    def getVelocity(self) -> vec2:
        return self.velocity
    
    def setDisplacement(self, displ) -> None:
        self.displace = displ
        self.displace.x %= self.tileDimensions.x
        self.displace.y %= self.tileDimensions.y


    def setColor(self, oldColor, newColor):
        self.tileImage = palette_swap(self.tileImage, oldColor, newColor)

        self.adaptChanges()


    def setScale(self, scale):
        self.scale = scale
        self.tileImage = loadImage(self.patternid, self.scale)
        self.adaptChanges()

    def getScale(self):
        return self.scale
    


    def adaptChanges(self):
        self.tileDimensions = vec2(self.tileImage.get_width(), self.tileImage.get_height())

        self.numTiles = vec2(0,0)
        self.numTiles.x = (self.resolution.x//self.tileDimensions.x)+ abs(self.offsetTile.x)*self.buffer + 1
        self.numTiles.y = (self.resolution.y//self.tileDimensions.y)+ abs(self.offsetTile.x)*self.buffer + 1

        width = self.numTiles.x * self.tileDimensions.x
        height =  self.numTiles.y * self.tileDimensions.y

        self.decoySurf = pygame.Surface((int(width), int(height)))
        self.decoySurf.fill((0,0,0))

        self._drawtoSurf(self.decoySurf)

    def update(self, dt):

        self.displace.x += self.velocity.x*dt
        self.displace.y += self.velocity.y*dt

        self.displace.x %= self.tileDimensions.x
        self.displace.y %= self.tileDimensions.y

    def draw(self, window):
        posx = self.displace.x - abs(self.offsetTile.x*self.tileDimensions.x)
        posy = self.displace.y - abs(self.offsetTile.y*self.tileDimensions.y)
        window.blit(self.decoySurf, (posx, posy))


    def tile_draw(self, window):
        for x in range(int(self.numTiles.x)):
            for y in range(int(self.numTiles.y)):
                posx = self.displace.x + x*self.tileDimensions.x + self.offsetTile.x*self.tileDimensions.x
                posy = self.displace.y + y*self.tileDimensions.y + self.offsetTile.y*self.tileDimensions.y
                window.blit(self.tileImage, (posx, posy))


    def _drawtoSurf(self, surf):
        for x in range(int(self.numTiles.x)):
            for y in range(int(self.numTiles.y)):
                posx = x*self.tileDimensions.x 
                posy =  y*self.tileDimensions.y 
                surf.blit(self.tileImage, (posx, posy))


### end


### minesweeper class
class Minesweeper:
    def __init__(self, res, actualRes):
        self.res = res
        self.actRes = actualRes

        self.colors = [(20, 17, 21), (155, 41, 21), (240, 239, 244), (160, 159, 184),(21, 96, 100)]

        self.display = pygame.Surface(res)
        self.display.fill((0,0,0))
        self.display.set_colorkey(self.colors[0])
        self.displayRect = self.display.get_rect(center=self.actRes//2)
        self.pos = vec2(*self.displayRect.topleft)

        self.outlines = pygame.Surface(res)
        self.outlines.fill((0,0,0))

        
        self.gameOver = False
        self.gameState = None

        
        self.cellSize  = vec2(64, 64)
        self.numCells = vec2(self.res.x//self.cellSize.x, self.res.y//self.cellSize.y)
        self.totalTiles = self.numCells.x * self.numCells.y

        self.totalMines = -1
        self.mineMin = self.totalTiles * 10/100 ### percent of the total tiles
        self.mineMax = self.totalTiles * 20/100 ### percent of the total tiles

        self.grid = []

        self.depthIncrease = 0.3 ### delay time increase
        self.depthBase = 0.5 ## the first clicked cell has this delay time
        self.depthFactor = 1/2 ### delay time increase factor
     
        self.scale = (self.cellSize.x-16) // 16
        self.images = [loadImage(f"assets/{i}.png", self.scale) for i in range(0, 10)]

        self.flagImage = loadImage(f"assets/signboard2.png", self.scale)
        self.hoverImage = loadImage(f"assets/hoverCrosshair1.png", self.cellSize.x // 16)

        self.mineImage = loadImage(f"assets/signboard6.png", self.scale)
        self.revealMines = False
        self.minesRevealed = False
        self.mineRevealTimer = Timer(0.3)

        self.errorSfx = pygame.mixer.Sound("assets/error.ogg")
        self.errorSfxPlayed = False

        self.generate()

    def setPos(self, pos):
        self.displayRect.center = pos
        self.pos = vec2(*self.displayRect.topleft)

    def generate(self):
        self.grid.clear()

        self.numMines = random.randint(int(self.mineMin), int(self.mineMax))
        print(self.numMines)

        self.minePos = []

        for _ in range(self.numMines):
            x = random.randint(0, int(self.numCells.x)-1)
            y = random.randint(0, int(self.numCells.y)-1)

            if (x,y) in self.minePos:
                while (x, y) in self.minePos:
                    x = random.randint(0, int(self.numCells.x)-1)
                    y = random.randint(0, int(self.numCells.y)-1)

            # if (x, y) not in self.minePos:
            self.minePos.append((x,y))
                
        print(self.minePos)
        
        for y in range(int(self.numCells.y)):

            self.grid.append([])

            for x in range(int(self.numCells.x)):

                if (x, y) in self.minePos:
                    self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize, "mine"))

                else:
                    self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize))

        self.assignValues()

    def assignValues(self):
        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                # print(y,x, len(grid))
                cell = self.grid[y][x]

                numMines = 0
                neighBours = 0
                
                if cell.type == "none":
                    for i in range(y-1, y+2):
                        for j in range(x-1, x+2):
                            if (i >= 0 and j >= 0):
                                if (i < len(self.grid) and j < len(self.grid[y])):
                                    if self.grid[i][j].type == "mine":
                                        numMines += 1
                            neighBours += 1
                else:
                    numMines = "x"

                cell.setHoverImage(self.hoverImage)
                cell.setFlagImage(self.flagImage, self.colors[3])

                if numMines != 0 and numMines != "x":
                    cell.setValue(numMines, self.images[numMines])

                elif numMines == "x":
                    cell.setValue(numMines, self.mineImage)
                
    def startRevealing(self, x, y, depth):
        ### check if the point or eleemnt is in the bounds 
        if x < 0 or x >= len(self.grid[0]):
            return -1
        if y < 0 or y >= len(self.grid):
            return -1
        

        ### ensuring we do not go again on a cell already checked
        if not self.grid[y][x].goingToBeRevealed:

            if self.grid[y][x].value != 0:
                self.grid[y][x].reveal(self.depthBase + depth*self.depthFactor)
                
            elif self.grid[y][x].value == 0:

                self.grid[y][x].reveal(self.depthBase + depth*self.depthFactor)

                self.startRevealing(x-1, y-1, depth + self.depthIncrease)
                self.startRevealing(x-1, y, depth + self.depthIncrease)
                self.startRevealing(x-1, y+1, depth + self.depthIncrease)

                self.startRevealing(x, y-1, depth + self.depthIncrease)
                self.startRevealing(x, y+1, depth + self.depthIncrease)

                self.startRevealing(x+1, y-1, depth + self.depthIncrease)
                self.startRevealing(x+1, y, depth + self.depthIncrease)
                self.startRevealing(x+1, y+1, depth + self.depthIncrease)
        
    def drawGrids(self, window):
        for i in range(int(self.numCells.x)):
            pygame.draw.line(window, self.colors[3], (i*self.cellSize.x, 0), (i*self.cellSize.x, res.y))

        for j in range(int(self.numCells.y)):
            pygame.draw.line(window, self.colors[3], (0, j*self.cellSize.y), (res.x, j*self.cellSize.y))

    def eventUpdate(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and self.gameOver:
                self.generate()

                self.gameOver = False
                self.gameOverStartAnim = False
                self.gameOverTimer = Timer(1.5)
                self.gameState = None


                self.restartText = self.font.render("Press [R] to continue", True, self.colors[2], None)
                self.restartTextBase = self.font.render("Press [R] to continue", True, self.colors[2], None)
                self.restartAnimRot = SineAnimation(5, 0.9)
                self.restartAnimScale = SineAnimation(0.15, 0.6, 1)
                self.restartTextRect = self.restartText.get_rect(center=(self.res.x//2, self.res.y*0.75))


                self.gameStateText = None
                self.gameTextRect = None


        if not self.gameOver:
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    xpos,ypos = pygame.mouse.get_pos()

                    if self.displayRect.collidepoint(xpos, ypos):

                        xpos -= self.pos.x 
                        ypos -= self.pos.y
                        y = int(ypos//self.cellSize.y) 
                        x = int(xpos//self.cellSize.x)

                        if self.grid[y][x].value == "x":
                            #### game over - lost
                            self.grid[y][x].reveal(self.depthBase)
                            self.revealMines = True

                            if not self.errorSfxPlayed:
                                self.errorSfx.play()
                                self.errorSfxPlayed = True
                        else:
                            self.startRevealing(x, y, 0)


                elif event.button == 3:
                    xpos,ypos = pygame.mouse.get_pos()

                    if self.displayRect.collidepoint(xpos, ypos):

                        xpos -= self.pos.x 
                        ypos -= self.pos.y
                        y = int(ypos//self.cellSize.y) 
                        x = int(xpos//self.cellSize.x)
                        if not self.grid[y][x].isRevealed:
                            self.grid[y][x].flagit()     

        # print(self.gameState)

    def updateAndDraw(self,dt, window):

        self.display.fill(self.colors[0])
        self.outlines.fill(self.colors[0])
        self.cellsNonRevealed = 0


        if self.revealMines:
            self.mineRevealTimer.update(dt)
            if self.mineRevealTimer.isOver():
                self.mineRevealTimer.reset()
                if len(self.minePos) > 0:
                    self.grid[self.minePos[0][1]][self.minePos[0][0]].reveal(self.depthBase)
                    self.minePos.pop(0)
                    ### sfx
                else:
                    self.minesRevealed = True
                    self.revealMines = False

        if self.minesRevealed:
            self.gameOver = True 
            self.gameState = "lost"


        self.cellsNonRevealed = 0

        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                if not self.gameOver:
                    self.grid[y][x].update(dt, self.pos)

                self.grid[y][x].draw(self.display)
                self.grid[y][x].drawOutline(self.outlines)
                

                if not (self.grid[y][x].isRevealed or self.grid[y][x].goingToBeRevealed):
                    self.cellsNonRevealed += 1

            if not self.gameOver and not self.revealMines and not self.minesRevealed:
                if self.cellsNonRevealed == self.numMines:
                    self.gameOver = True 
                    self.gameState = "won"




        self.drawGrids(self.display)
        
        window.blit(self.outlines, self.displayRect)
        window.blit(self.display, self.displayRect)
        pygame.draw.rect(window, self.colors[3], self.displayRect, 3)

class Mainmenu:
    def __init__(self, res, actualRes):
        self.res = res
        self.actRes = actualRes

        self.colors = [(20, 17, 21), (155, 41, 21), (240, 239, 244), (160, 159, 184),(21, 96, 100)]

        self.display = pygame.Surface(res)
        self.display.fill((0,0,0))
        self.display.set_colorkey(self.colors[0])
        self.displayRect = self.display.get_rect(center=self.actRes//2)
        self.pos = vec2(*self.displayRect.topleft)

        self.outlines = pygame.Surface(res)
        self.outlines.fill((0,0,0))


        self.cellSize  = vec2(64, 64)
        self.numCells = vec2(self.res.x//self.cellSize.x, self.res.y//self.cellSize.y)

        self.grid = []

        self.alphabets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x','y', 'z', "!"]
        self.scale = (self.cellSize.x-16) // 16
        self.letters = [loadImage(f"assets/{self.alphabets[i]}.png", self.scale) for i in range(0, 26)]
        self.letters.append(loadImage("assets/exclaim.png", self.scale))
        
        self.minePos = vec2(3, 2)
        self.sweepPos = vec2(1, 5)
        self.timeGap = 0.3

    
        self.flagImage = loadImage(f"assets/signboard2.png", self.scale)
        self.hoverImage = loadImage(f"assets/hoverCrosshair1.png", self.cellSize.x // 16)

        self.shownTitle = False
        self.showTitleTimer = Timer(6)

        self.showOver = False
        self.showDone = False
        self.resetted = False

        self.generate()
    def setPos(self, pos):
        self.displayRect.center = pos
        self.pos = vec2(*self.displayRect.topleft)

    def generate(self):
        self.grid.clear()

        for y in range(int(self.numCells.y)):

            self.grid.append([])

            for x in range(int(self.numCells.x)):
                self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize))

        self.assignValues()

    def alphaIndex(self, letter):
        return self.letters[self.alphabets.index(str(letter))]

    def assignValues(self):
        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                # print(y,x, len(grid))
                cell = self.grid[y][x]
                cell.setHoverImage(self.hoverImage)
                cell.setFlagImage(self.flagImage, self.colors[3])

    def eventUpdate(self, event):
        pass


    def resetTiles(self):
            pass
    
    def revealThem(self):
        pass

    def drawGrids(self, window):
        for i in range(int(self.numCells.x)):
            pygame.draw.line(window, self.colors[3], (i*self.cellSize.x, 0), (i*self.cellSize.x, res.y))

        for j in range(int(self.numCells.y)):
            pygame.draw.line(window, self.colors[3], (0, j*self.cellSize.y), (res.x, j*self.cellSize.y))

    def updateAndDraw(self, dt, window):
        self.display.fill(self.colors[0])
        self.outlines.fill(self.colors[0])

        if not self.shownTitle:
            self.showTitleTimer.update(dt)

            time = self.showTitleTimer.percentCompleted()*self.showTitleTimer.duration

            count = 0

            ## mine

            if near(time, 0.5):
                self.grid[int(self.minePos.y)][int(self.minePos.x)].setValue("M", self.alphaIndex("m"))
                self.grid[int(self.minePos.y)][int(self.minePos.x)].reveal()
                count += 1
            else:
                count += 1
                
            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 1].setValue("I", self.alphaIndex("i"))
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 1].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 2].setValue("N", self.alphaIndex("n"))
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 2].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 3].setValue("E", self.alphaIndex("e"))
                self.grid[int(self.minePos.y)][int(self.minePos.x) + 3].reveal()
                count += 1
            else:
                count += 1


            ### sweeper

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x)].setValue("I", self.alphaIndex("s"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x)].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 1].setValue("I", self.alphaIndex("w"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 1].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 2].setValue("N", self.alphaIndex("e"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 2].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 3].setValue("E", self.alphaIndex("e"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 3].reveal()
                count += 1
            else:
                count += 1


            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 4].setValue("N", self.alphaIndex("p"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 4].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 5].setValue("N", self.alphaIndex("e"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 5].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 6].setValue("E", self.alphaIndex("r"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 6].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 7].setValue("E", self.alphaIndex("!"))
                self.grid[int(self.sweepPos.y)][int(self.sweepPos.x) + 7].reveal()
                count += 1
            else:
                count += 1
            if self.showTitleTimer.isOver():
                self.showOver = True

        if self.showOver and not self.resetted:
            self.resetTiles()
            self.revealThem()
            self.resetted = True
            self.showDone = True


        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                self.grid[y][x].draw(self.display)
                self.grid[y][x].drawOutline(self.outlines)
                self.grid[y][x].update(dt, self.pos)
                

        self.drawGrids(self.display)
        
        window.blit(self.outlines, self.displayRect)
        window.blit(self.display, self.displayRect)
        pygame.draw.rect(window, self.colors[3], self.displayRect, 3)


class EndMenu:
    def __init__(self, res, actualRes):
        self.res = res
        self.actRes = actualRes

        self.colors = [(20, 17, 21), (155, 41, 21), (240, 239, 244), (160, 159, 184),(21, 96, 100)]

        self.display = pygame.Surface(res)
        self.display.fill((0,0,0))
        self.display.set_colorkey(self.colors[0])
        self.displayRect = self.display.get_rect(center=self.actRes//2)
        self.pos = vec2(*self.displayRect.topleft)

        self.outlines = pygame.Surface(res)
        self.outlines.fill((0,0,0))


        self.cellSize  = vec2(64, 64)
        self.numCells = vec2(self.res.x//self.cellSize.x, self.res.y//self.cellSize.y)

        self.grid = []

        self.alphabets = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x','y', 'z', "!"]
        self.scale = (self.cellSize.x-16) // 16
        self.letters = [loadImage(f"assets/{self.alphabets[i]}.png", self.scale) for i in range(0, 26)]
        self.letters.append(loadImage("assets/exclaim.png", self.scale))
        
        self.youPos = vec2(3, 2)
        self.statePos = vec2(2, 5)
        self.timeGap = 0.3

    
        self.flagImage = loadImage(f"assets/signboard2.png", self.scale)
        self.hoverImage = loadImage(f"assets/hoverCrosshair1.png", self.cellSize.x // 16)

        self.shownTitle = False
        self.showTitleTimer = Timer(6)

        self.showOver = False
        self.showDone = False
        self.resetted = False

        self.gameState = None

        self.generate()

    def setPos(self, pos):
        self.displayRect.center = pos
        self.pos = vec2(*self.displayRect.topleft)

    def generate(self):
        self.grid.clear()

        for y in range(int(self.numCells.y)):

            self.grid.append([])

            for x in range(int(self.numCells.x)):
                self.grid[y].append(Cell(vec2(x*self.cellSize.x, y*self.cellSize.y), self.cellSize))

        self.assignValues()

    def alphaIndex(self, letter):
        return self.letters[self.alphabets.index(str(letter))]

    def assignValues(self):
        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                # print(y,x, len(grid))
                cell = self.grid[y][x]
                cell.setHoverImage(self.hoverImage)
                cell.setFlagImage(self.flagImage, self.colors[3])

    def eventUpdate(self, event):
        pass

    def setState(self, state):
        self.gameState = state


    def resetTiles(self):
            pass
    
    def revealThem(self):
        pass

    def drawGrids(self, window):
        for i in range(int(self.numCells.x)):
            pygame.draw.line(window, self.colors[3], (i*self.cellSize.x, 0), (i*self.cellSize.x, res.y))

        for j in range(int(self.numCells.y)):
            pygame.draw.line(window, self.colors[3], (0, j*self.cellSize.y), (res.x, j*self.cellSize.y))

    def updateAndDraw(self, dt, window):
        self.display.fill(self.colors[0])
        self.outlines.fill(self.colors[0])

        if not self.shownTitle and self.gameState:
            self.showTitleTimer.update(dt)

            time = self.showTitleTimer.percentCompleted()*self.showTitleTimer.duration

            count = 0

            ## mine

            if near(time, 0.5):
                self.grid[int(self.youPos.y)][int(self.youPos.x)].setValue("Y", self.alphaIndex("y"))
                self.grid[int(self.youPos.y)][int(self.youPos.x)].reveal()
                count += 1
            else:
                count += 1
                
            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.youPos.y)][int(self.youPos.x) + 1].setValue("O", self.alphaIndex("o"))
                self.grid[int(self.youPos.y)][int(self.youPos.x) + 1].reveal()
                count += 1
            else:
                count += 1

            if near(time, 0.5 + self.timeGap*count):
                self.grid[int(self.youPos.y)][int(self.youPos.x) + 2].setValue("N", self.alphaIndex("u"))
                self.grid[int(self.youPos.y)][int(self.youPos.x) + 2].reveal()
                count += 1
            else:
                count += 1

            ### sweeper

            if self.gameState == "lost":
                self.statePos.x = 2
                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x)].setValue("I", self.alphaIndex("l"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x)].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 1].setValue("I", self.alphaIndex("o"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 1].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 2].setValue("N", self.alphaIndex("s"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 2].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 3].setValue("E", self.alphaIndex("t"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 3].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 4].setValue("E", self.alphaIndex("!"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 4].reveal()
                    count += 1
                else:
                    count += 1

            if self.gameState == "won":
                self.statePos.x = 3
                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x)].setValue("I", self.alphaIndex("w"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x)].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 1].setValue("I", self.alphaIndex("o"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 1].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 2].setValue("N", self.alphaIndex("n"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 2].reveal()
                    count += 1
                else:
                    count += 1

                if near(time, 0.5 + self.timeGap*count):
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 4].setValue("E", self.alphaIndex("!"))
                    self.grid[int(self.statePos.y)][int(self.statePos.x) + 4].reveal()
                    count += 1
                else:
                    count += 1


            if self.showTitleTimer.isOver():
                self.showOver = True

        if self.showOver and not self.resetted:
            self.resetTiles()
            self.revealThem()
            self.resetted = True
            self.showDone = True


        for y in range(int(self.numCells.y)):
            for x in range(int(self.numCells.x)):
                self.grid[y][x].draw(self.display)
                self.grid[y][x].drawOutline(self.outlines)
                self.grid[y][x].update(dt, self.pos)
                

        self.drawGrids(self.display)
        
        window.blit(self.outlines, self.displayRect)
        window.blit(self.display, self.displayRect)
        pygame.draw.rect(window, self.colors[3], self.displayRect, 3)


res = vec2(1280,724)

window = pygame.display.set_mode(res)


icon = loadImage("assets/icon.png")
pygame.display.set_icon(icon)

pygame.display.set_caption("Minesweeper!")

clock = pygame.time.Clock()
dt = 1/60
fps = 60

gridSize = vec2(640, 640)

mm = Mainmenu(gridSize, res)
ms = Minesweeper(gridSize, res)
em = EndMenu(gridSize, res)
# ms.setPos(vec2(3*mm.pos.x, mm.pos.y))


pattern = PatternBg(res)
pattern.setScale(1)

pattern.setColor((0,0,0), ms.colors[0])
pattern.setColor((255,255,255), ms.colors[4])
pattern.setVelocity(vec2(150,50))

angle = 0
pos1x, pos1y = ms.displayRect.center
pos2x, pos2y = mm.displayRect.center

transTimer = Timer(1)
transitionState = "none"
mainMenu = True
mineSweeper = False
transitionDone = False
endMenu = False


bgm = pygame.mixer.Sound("assets/bgm.ogg")
bgm.set_volume(0.5)
bgm.play(loops=-1)

woosh = pygame.mixer.Sound("assets/swoosh.ogg")
woosh.set_volume(0.7)

while 1:
    clock.tick(1000000)
    window.fill(ms.colors[0])


    fps = clock.get_fps() 

    dt = 1/fps if fps else 1/60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        
    if endMenu:
        em.eventUpdate(event)

    if mainMenu:
        mm.eventUpdate(event)

    if mineSweeper:
        ms.eventUpdate(event)
        
        
    
    pattern.update(dt)
    pattern.draw(window)

    if endMenu:
        em.updateAndDraw(dt, window)



    if mineSweeper:
        ms.updateAndDraw(dt, window)

        if ms.gameState and ms.gameOver and transitionState == "none":
            em.setState(ms.gameState)
            transitionState = "game-to-end"
            pos1x, pos1y = em.displayRect.center
            pos2x, pos2y = ms.displayRect.center
            woosh.play()

    
    if mainMenu:
        mm.updateAndDraw(dt, window)

        if mm.showDone and transitionState == "none":
            transitionState = "main-to-game"
            pos1x, pos1y = ms.displayRect.center
            pos2x, pos2y = mm.displayRect.center
            woosh.play()

    if transitionState == "main-to-game":
        mineSweeper = True
        transTimer.update(dt)

        factor = transTimer.percentCompleted()

        mm.setPos(vec2(pos2x - 2*pos2x*factor, pos2y))
        ms.setPos(vec2(res.x + pos2x - 2*pos2x*factor, pos2y))

        if transTimer.isOver():
            mainMenu = False
            mineSweeper = True
            transitionState = "none"
            transTimer.reset()

    if transitionState == "game-to-end":
        endMenu = True
        transTimer.update(dt)

        factor = transTimer.percentCompleted()

        ms.setPos(vec2(pos2x - 2*pos2x*factor, pos2y))
        em.setPos(vec2(res.x + pos2x - 2*pos2x*factor, pos2y))

        if transTimer.isOver():
            mineSweeper = False
            endMenu = True
            transitionState = "none"
            transTimer.reset()





    

    pygame.display.flip()

