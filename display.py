from typing import Optional, Callable
from random import randint

import pygame
from pygame.locals import *

class ChestDisplay: # Nathan
    def __init__(self, surface:pygame.Surface, pos:tuple, size:tuple, closed:bool = True, clock:Optional[pygame.time.Clock] = None):
        self.surface = surface
        self.pos = pos
        self.size = size
        self.frame = 0
        self.image = 1 if closed else 15
        self.img_f = 2
        self._last_loaded = None
        self.closed = closed
        self.load(self.image)

        self.clock = clock
        self.time = 0
        self.ended = False

    def display(self, surface:Optional[pygame.Surface] = None, pos:Optional[tuple] = None, size:Optional[tuple] = None, delay=20):
        surface = surface or self.surface
        pos = pos or self.pos
        size = size or self.size
        assert not (surface is None or pos is None or size is None), "Arguments non fournis"

        elapsed = self.clock.get_time() if self.clock is not None else delay
        self.time += elapsed

        steps = self.time // delay
        if steps > 0:
            self.time = self.time % delay
            self.frame += steps
            n_images = self.frame // self.img_f
            if n_images > 0:
                if self.closed:
                    self.image = max(1, self.image - n_images)
                else:
                    self.image = min(15, self.image + n_images)
                self.frame = self.frame % self.img_f
        self.ended = (self.image >= 15 and not self.closed) or (self.image <= 1 and self.closed)
        self.load(self.image)
        surface.blit(self.chest_image, (pos[0], pos[1]))

    def load(self, n):
        if n == self._last_loaded:
            return
        self.chest_image = pygame.image.load(f"assets/images/chest/chest{str(self.image)}.png")
        self.chest_image = pygame.transform.scale(self.chest_image, (self.size[0], self.size[1]))
        self._last_loaded = n

class TextDisplay: #Abel
    """
    Affiche du texte progressivement à l'écran.

    Attributes:
    ----------
        txt (str): Le texte à afficher.
        fenetre (pygame.Surface): La surface sur laquelle afficher le texte.
        clock (pygame.time.Clock): L'horloge pour gérer le timing.
        police (int): La taille de la police.
        color (tuple): La couleur du texte.
        pos (tuple): La position d'affichage.
        size (tuple): La taille de la zone d'affichage.
        background_color (tuple, optional): La couleur de fond de la zone d'affichage.
    """
    def __init__(self,txt:str, fenetre:pygame.Surface, clock:pygame.time.Clock, police:int = 40, color:tuple = (0,0,0), pos:tuple = (None,None), size:tuple = (None,None), background_color:Optional[tuple] = None): 
        self.txt = f'*{txt}*'
        self.mot = self.txt.split(' ')[0]
        self.color = color
        self.background_color = background_color
        self.frames = 0	#len(self.txt*pygame.time.get_ticks())
        self.end = False
        self.time = 0
        self.x,self.y = pos if pos!=(None,None) else (10,fenetre.get_height()/1.5)
        w,h = pygame.display.get_surface().get_size()
        self.size = (w, 1/3*h) if size == (None,None) else size
        self.bloc = pygame.Rect((self.x,self.y), self.size)

        self.my_font = pygame.font.SysFont('Consolas', police)
        self.fenetre = fenetre
        self.clock = clock
        self.blocliste = [pygame.Rect((self.x+5,self.y+5), (self.size[0]-20, self.my_font.get_height()))]

        cur_w = 0
        cur_l = 0
        self.txts = [""]

        for mot in self.txt.split(' '):
            if (len(mot) + cur_w ) * self.my_font.size("a")[0] >= self.size[0] - 20 or mot == "&":
                cur_l += 1
                self.txts.append("")
                self.blocliste.append(pygame.Rect((self.x+15,self.y+cur_l*(self.my_font.get_height()+5)), (self.size[0]-20, self.my_font.get_height())))
                cur_w = 0

            if mot == "&":
                continue

            self.txts[cur_l] += mot + " "
            cur_w += len(mot) + 1

    def display(self,delay=20):	#affiche le texte progressivement, delay est le temps entre chaque caractère en ms
        if self.background_color is not None:
            pygame.draw.rect(self.fenetre,self.background_color,self.bloc)
        else:
            pygame.draw.rect(self.fenetre,(255,0,0),self.bloc)
        cur_txt_prog = 0
        for txt, bloc in zip(self.txts, self.blocliste):
            self.fenetre.blit(self.my_font.render(txt[:max(0, min(self.frames - cur_txt_prog, len(txt) - 1))], True, self.color), bloc)
            cur_txt_prog += len(txt)
        if self.time>=delay and not self.end:
            self.frames = self.frames+self.time//delay
            self.time = 0
        self.time += self.clock.get_time()
        self.end = self.frames>=len(self.txt)
    
    def reset(self):    #remet le texte à zéro
        self.frames = 0
        self.time = 0
        self.end = False

class MouseButton: # Nathan
    def __init__(self, text, pos, size, action:Callable, screen:pygame.Surface, position:tuple = (0, 0)): # Lino
        """
        Stocker le text, la pos, la taille, l'action et la fenêtre
        action correspond à la fonction qui doit être lancée à l'appui -> on peut l'appeler comme ça : action()
        """
        self.text = text
        self.pos = pos
        self.size = size
        self.action = action
        self.screen = screen
        self.background = pygame.Rect(pos, size)
        self.position = position

    def display(self):
        """Affiche le rectangle, ses contours et le texte d'une couleur ou d'une autre si la souris passe dessus"""
        mouse_pos = pygame.mouse.get_pos()
        local_mouse_pos = (mouse_pos[0] - self.position[0], mouse_pos[1] - self.position[1])
        hovered = self.background.collidepoint(local_mouse_pos)
        color = (255, 120, 87) if not hovered else (239, 255, 94)

        pygame.draw.rect(self.screen, (0,0,0), self.background)

        pygame.draw.rect(self.screen, color, self.background, 2)

        font = pygame.font.SysFont('Lucida Console', int(self.size[1] * 0.6))
        text_surf = font.render(self.text, True, color)
        text_rect = text_surf.get_rect(center=self.background.center)
        self.screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            local_pos = (event.pos[0] - self.position[0], event.pos[1] - self.position[1])
            if self.background.collidepoint(local_pos):
                self.action()

class RoomDisplay: # Abel
    """
    Classe gérant l'affichage du fond de la salle, de l'ombre et de l'animation de la porte.

    Attributes:
    ----------
        screen (pygame.Surface): La surface sur laquelle afficher les éléments.
        taille (float): Le pourcentage de la taille de l'écran à utiliser pour l'affichage.
    """
    def __init__(self,screen,taille=70):
        self.taille=taille/100
        self.screen = screen

        self.bg = pygame.image.load('assets\\images\\background\\Salle_fond.png')
        self.shade = pygame.image.load('assets\\images\\background\\Shade.png')
        self.enter = pygame.image.load('assets\\images\\background\\Porte_Ouverte.png')

        self.w,self.h = pygame.display.get_surface().get_size()
        self.bg = pygame.transform.scale(self.bg, (int(self.w*self.taille),int(self.h*self.taille)))
        self.shade = pygame.transform.scale(self.shade, (int(self.w*self.taille),int(self.h*self.taille)))
        self.enter = pygame.transform.scale(self.enter, (int(self.w*self.taille),int(self.h*self.taille)))

        self._enter_showing = False
        self._enter_end_time = 0
        self._enter_pos = (self.w*(1-self.taille)/2, 0)

    @property # Nathan
    def enter_animation(self):  
        return self._enter_showing

    def display_bg(self):   #affiche le fond de la salle
        self.screen.fill((0,0,0))
        self.screen.blit(self.bg,(self.w*(1-self.taille)/2,0))

    def display_shade(self):    #affiche l'ombre de la salle
        self.screen.blit(self.shade,(self.w*(1-self.taille)/2,0))

    def display_enter(self):
        """Appeler chaque frame : affiche 'enter' si le timer est actif."""
        if not self._enter_showing:
            return
        self.screen.blit(self.enter, self._enter_pos)
        if pygame.time.get_ticks() >= self._enter_end_time:
            self._enter_showing = False

    def start_enter(self, duration_ms: int = 500):
        """Commence l'affichage de l'image 'enter' pendant duration_ms millisecondes."""
        self._enter_showing = True
        self._enter_end_time = pygame.time.get_ticks() + int(duration_ms)

class EnnemiDisplay: # Abel
    """
    Classe gérant l'affichage d'un ennemi.

    Attributes:
    ----------
        surface (pygame.Surface): La surface sur laquelle afficher les éléments.
        pos (tuple): La position à laquelle l'image doit être affichée.
        size (float): Le pourcentage de la taille de l'écran à utiliser pour l'affichage de l'image.
        image_path (str): Le chemin de l'image.
    """
    def __init__(self, surface:pygame.Surface, pos:tuple, size:int, image_path:str):
        self.surface = surface
        self.pos = pos
        self.size = size
        self._last_loaded = None
        self.load(image_path)

    def display(self):  #affiche l'ennemi
        self.surface.blit(self.ennemi_image, (self.pos[0], self.pos[1]))

    def display_damage(self):   #affiche l'ennemi en train de subir des dégats
        self.surface.blit(self.ennemi_image, (self.pos[0] + randint(-10, 10), self.pos[1] + randint(-10, -5)))
        self.load(self._last_loaded)

    def load(self, image_path): #charge l'image de l'ennemi
        self.ennemi_image = pygame.image.load(image_path)
        self.width, self.height = self.ennemi_image.get_size()
        self.ennemi_image = pygame.transform.scale(self.ennemi_image, (int(self.size * self.width), int(self.size * self.height)))
        self._last_loaded = image_path

class HealthBar: # Lino
    """Barre de vie à afficher"""

    def __init__(self, personnage, pos:tuple, size:tuple, surface:pygame.Surface):
        """
        personnage:Personnage -> barre de vie reliée au personnage
        pos -> position (x, y)
        """
        self.personnage = personnage
        self.pos = pos
        self.size = size# Initier variables
        self.surface = surface

        self.fond_color = (50, 50, 50)
        self.pv_color = (0, 255, 0)  # Initier le bloc de fond à taille size

    def display(self):
        pygame.draw.rect(self.surface, self.fond_color,(self.pos[0], self.pos[1], self.size[0], self.size[1]))# Afficher le rectangle du fond

        rectangle_pv = self.size[0] * self.personnage.pv / self.personnage.get_max_pv()
        pygame.draw.rect(self.surface, self.pv_color, (self.pos[0], self.pos[1], rectangle_pv, self.size[1]))

class ItemDisplay: # Hugo
    def __init__(self, surface: pygame.Surface, pos: tuple, size: tuple, object):
        # Initialise toutes les variables comme attributs
        self.surface = surface
        self.pos = pos
        self.size = size
        self.object_type = object.type
        self.object = object

        # Créer le fond d’écran avec pygame.Rect
        self.background_rect = pygame.Rect(pos, size)
        self.background_color = (50, 50, 50)  # gris foncé

        # Créer l’image avec self._load_image, centrée dans le fond
        self.image = self._load_image(self.object_type)
        self.image_rect = self.image.get_rect(center=self.background_rect.center)

    def display(self):
        # Affiche le fond puis l’image
        pygame.draw.rect(self.surface, self.background_color, self.background_rect)
        self.surface.blit(self.image, self.image_rect)

    def _load_image(self, object_type): # aide Nathan
        if object_type == "potion":
            image = pygame.image.load("assets/images/health_potion.png").convert_alpha()
        elif object_type == "arme":
            object_name = self.object.nom.lower()
            if object_name == "lance":
                image = pygame.image.load("assets/images/weapon/Spear.png").convert_alpha()
            elif object_name == "epée":
                image = pygame.image.load("assets/images/weapon/Sword.png").convert_alpha()
        elif object_type == "armure":
            image = pygame.image.load("assets/images/Armor.png").convert_alpha()
        else:
            # Image par défaut si l’objet est inconnu
            image = pygame.Surface((50, 50))
            image.fill((200, 0, 0))

        image = resize(image, self.size)

        return image

def resize(image:pygame.Surface, size:tuple) -> pygame.Surface:   #redimensionne une image en gardant les proportions
    iw, ih = image.get_size()
    if iw == 0 or ih == 0:
        target_w, target_h = size
    else:
        scale = min(size[0] / iw, size[1] / ih)
        target_w = max(1, int(iw * scale))
        target_h = max(1, int(ih * scale))
    image = pygame.transform.scale(image, (target_w, target_h))
    return image

def get_size(surface:pygame.Surface, pourcentage:float, size:str = "width") -> float:
    """Renvoie la valeur en pixel qui correspond au pourcentage de la dimension de la surface"""
    assert size == "width" or size == "height", f"Dimension {size} non disponible"
    val = surface.get_size()[0 if size == "width" else 1]

    return int(pourcentage * val / 100)

def get_dialogue_text(text:str, monster, screen:pygame.Surface, clock:pygame.time.Clock) -> TextDisplay:
    """monster:Monstre -> contient un attribut ennemi_display"""
    size = (get_size(screen, 10), get_size(screen, 15, "height"))
    pos = (get_size(screen, 55), get_size(screen, 2, "height"))

    text_display = TextDisplay(text, screen, clock, pos=pos, size=size,background_color=(255, 255, 255), police=20)
    return text_display

class Credits : # Hugo aide de Nathan
    MAX = 10
    def __init__(self,text:list, fenetre:pygame.Surface, clock:pygame.time.Clock, scroll_speed = 10):
        self.texts = text
        self.fenetre = fenetre
        self.clock = clock

        self.scroll_speed = scroll_speed

        self.credits_surface = pygame.Surface((get_size(self.fenetre, 100), get_size(self.fenetre, 100, "height")))
        self.credits_surface.fill((0,0,0))
        self.pos = (0, get_size(self.fenetre, 100, "height"))
        self.add_text()
        self.end = False

    def display(self):
        self.fenetre.blit(self.credits_surface, self.pos)

        self.pos = (self.pos[0], self.pos[1] - self.scroll_speed)
        if self.pos[1] <= -self.credits_surface.get_size()[1]:
            self.end = True

    def add_text(self, space_percent = 10):
        height = get_size(self.fenetre, 100-space_percent, "height") // self.MAX
        self.my_font = pygame.font.SysFont('Comic Sans MS', 20)
        current_space = space_percent // self.MAX

        self.credits_surface = pygame.Surface((get_size(self.fenetre, 100), (height + current_space) * (len(self.texts) + 1)))
        self.credits_surface.fill((0,0,0))

        for idx, text in enumerate(self.texts, start=1):
            text_obj = self.my_font.render(text, True, (255,255,255))
            text_rect = text_obj.get_rect(center=(get_size(self.credits_surface, 50), (height + current_space) * idx))
            self.credits_surface.blit(text_obj, text_rect)

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()

    running=True
    fenetre = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    clock = pygame.time.Clock()

    texte = 'une petite prairie jolie, et des petites fleurs y poussait. En frolant cette pelouse, vous remarquez un arbre'
    monstre1 = EnnemiDisplay(fenetre, (get_size(fenetre,40),100), 1, "assets/images/monster/Perso_2.png")

    test=TextDisplay(texte, fenetre, clock, 15)
    background = RoomDisplay(fenetre)
    button = MouseButton("Test", (0,0), (100, 50), lambda : print("test"), fenetre)

    # Utiliser Credits pour afficher un bloc de textes
    credits_texts = [
        "Crédit : Développement - VotreNom",
        "Crédit : Graphismes - NomArtiste",
        "Crédit : Musique - NomMusicien",
        "TEST",
        "TESTSV",
        "TESTSTSTS",
        "TESTFBFBLEFE",
        "FHEGBIGB",
        "ougbigb",
        "fbeçfguibg",
        "ugiobhrigub",
        "oughigubheig",
        "oegfbioeube",
        "fiugiefeigfegveigvze",
        "ifbifbfiuebfeiuf",
        "ofhiouheoiefeuiofbeiuf",
        "foemifbneofbembfebo",
        "Merci d'avoir joué !"
    ]
    credits = Credits(credits_texts, fenetre, clock,5)
    credits.add_text()  # remplit la surface interne des crédits

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z:
                    if test.end:
                        running = False
                    else:
                        test.frames = len(test.txt)
                if event.key == K_ESCAPE:
                    running = False
                if event.key == K_a:
                    background.start_enter()
            button.handle_event(event)
        background.display_bg()
        #test.display()
        background.display_shade()
        background.display_enter()
        # afficher les crédits (appel par frame)
        if credits.end:
            print("end")
            running = False
        credits.display()
        button.display()
        monstre1.display()
        #test.reset() if test.end and test.time >= 1000 else None
        pygame.display.update()
        clock.tick(60)

    pygame.quit()

def make_buttons(surface: pygame.Surface, actions: list, space_percent: int = 20, button_bloc_pos: tuple = (0, 0)) -> list: # Nathan
    """
    Crée et renvoie une liste de MouseButton pour la surface donnée.

    Parameters
    ----------
    surface: pygame.Surface
        Surface sur laquelle les boutons seront dessinés (utilisée pour calculs de taille).
    actions: list
        Liste de tuples (label: str, callback: Callable).
    space_percent: int
        Pourcentage d'espace réservé autour des boutons (voir implémentation originale).
    button_bloc_pos: tuple
        Position (offset) en coordonnées fenêtre où la surface contenant les boutons est blittée.
    """
    if not actions:
        return []

    nb = len(actions)
    space = int(get_size(surface, space_percent) / (nb + 1))
    size = (int(get_size(surface, 100 - space_percent) / nb), int(get_size(surface, 100, "height")))

    buttons = []
    for idx, (button_txt, button_callable) in enumerate(actions, start=1):
        pos = (space * idx + size[0] * (idx - 1), 0)
        buttons.append(MouseButton(button_txt, pos, size, button_callable, surface, button_bloc_pos))

    return buttons