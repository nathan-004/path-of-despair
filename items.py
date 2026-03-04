from random import shuffle, choice, uniform

from constants import *
from display import *

def get_level(game) -> int: # Nathan
    """
    Utilise le niveau du joueur et l'anvancée dans le jeu pour déterminer un niveau
    """
    avancee_level = game.personnage.position[0] / game.map.width * MAX_LEVEL
    return max(min(int((avancee_level + game.personnage.level)/2 + randint(-1, 1)), MAX_LEVEL), 0)

def get_random_item_stats(game, type_:str) -> tuple: # Nathan
    """Renvoie un tuple (soin, degats, resistance) basé sur l'avancement du joueur et son niveau"""
    if game.map.name == "start":
        level = 0
    elif game.map.name == "end":
        level = 20
    else:
        level = get_level(game)

    soin, degats, resistance = 0,0,0

    if type_ == "potion":
        soin = PLAYER_BASE_ITEM_SOIN + level * PLAYER_ITEM_LEVEL_AUGMENTATION_SOIN
    elif type_ == "arme":
        degats = PLAYER_BASE_ATTACK + level * PLAYER_ITEM_LEVEL_AUGMENTATION_DEGATS
    elif type_ == "armure":
        resistance = PLAYER_BASE_ITEM_RES + level * PLAYER_ITEM_LEVEL_AUGMENTATION_RES

    return tuple([val * (1 + uniform(-0.3, 0.3)) for val in [soin, degats, resistance]])

def is_better(obj1, obj2) -> int: # Nathan
    """
    Renvoi si l'objet 1 est meilleur que l'objet 2
    < 0 si obj2 est meilleur
    > 1 si obj1 est meilleur
    0 s'ils sont équivalents
    """
    parameters = ["soin", "degat", "resistance"]
    obj1_n = 0
    obj2_n = 0

    for obj1_val, obj2_val in zip([getattr(obj1, par) for par in parameters], [getattr(obj2, par) for par in parameters]):
        obj1_n += int(obj1_val > obj2_val)
        obj2_n += int(obj2_val > obj1_val)

    return obj1_n - obj2_n

class Objet: # Hugo
    current_room = (0, 0)

    def __init__(self, nom, type_, soin=0, degat=0, resistance=0):
        self.nom = nom
        self.type = type_
        self.soin = soin
        self.degat = degat
        self.resistance = resistance
        self.last_used = None

    def use(self, personnage):
        """
        - Vérifie que l'objet n'a pas été utilisé dans la même salle
        - Ajoute les attributs de l'objet au personnage
        - Met à jour last_used
        """

        if self.last_used == self.current_room:
            return False

        personnage.pv += self.soin
        personnage.degat += self.degat
        personnage.resistance += self.resistance

        self.last_used = self.current_room

        return True

    def get_message(self) -> str:
        """
        Renvoie les stats de l'objet sous forme de texte.
        """
        message = f"{self.nom}, {self.type} {NEW_LINE_CHARACTER} "

        # Ajouter seulement les valeurs différentes de 0
        if self.soin != 0:
            message += f"Soin : +{self.soin:.1f} {NEW_LINE_CHARACTER} "
        if self.degat != 0:
            message += f"Dégâts : +{self.degat:.1f} {NEW_LINE_CHARACTER} "
        if self.resistance != 0:
            message += f"Résistance : +{self.resistance:2f} {NEW_LINE_CHARACTER} "

        return message

class Inventaire: # Hugo
    def __init__ (self):
        self.equipements = {}
        self.consommables = {}

    def add(self, obj: Objet):
        if obj.type.lower() == "potion":
            self.consommables[obj.type] = obj
        else:
            self.equipements[obj.type] = obj

    def equip(self, perso):
        for objet in self.equipements.values():
            perso.use(objet)

    def get(self, type_) -> Objet:
        if type_ in self.consommables:
            return self.consommables[type_]
        elif type_ in self.equipements:
            return self.equipements[type_]
        return Objet(None, None)

    def get_content(self) -> dict: # Nathan
        """Renvoie les informations à sauvegarder"""
        content = {
            "equipements": {
                obj.type: {"nom": obj.nom, "soin": obj.soin, "degat": obj.degat, "resistance": obj.resistance} for obj in self.equipements.values()
            },
            "consommables": {
                obj.type: {"nom": obj.nom, "soin": obj.soin, "degat": obj.degat, "resistance": obj.resistance} for obj in self.consommables.values()
            }
        }

        return content

    def load(self, content:dict): # Nathan
        for obj_type, obj in content["equipements"].items():
            self.equipements[obj_type] = Objet(obj["nom"], obj_type, obj["soin"], obj["degat"], obj["resistance"])
        for obj_type, obj in content["consommables"].items():
            self.consommables[obj_type] = Objet(obj["nom"], obj_type, obj["soin"], obj["degat"], obj["resistance"])

class Coffre: # Hugo
    """Permet de renvoyer un type d'objet aléatoire en fonction de ceux déjà renvoyés"""

    def __init__(self, n: int = 1, types: list = ["potion", "arme", "armure"]):
        """
        n: Nombre de tirages où l'on est sûr d'avoir le même nombre d'objets
        types: Nom des types d'objet à retourner
        """
        self.types = types  
        self.n = n        # Nombre de tirages avant répétition
        self.objets = []  # Contient la liste de types d'objet aléatoires
        self.item = None

        self.chest_display = None
        self.item_display = None
        self.text_display = None
        self.end = False
        self.buttons = None

        self.actions_end = False

    def get(self):
        """Retourne un type d'objet aléatoire"""
        if not self.objets:
            self.objets = self.types * self.n
            shuffle(self.objets)

        return self.objets.pop(0)

    def display(self, game, pos:tuple, size:tuple):
        if self.chest_display is None:
            self.open_animation(game.screen, pos, size)
        elif not self.chest_display.ended:
            self.open_animation(game.screen, pos, size)
        elif not self.actions_end:
            self.display_item_choice(game, pos, size)
        else:
            self.end = True

    def open_animation(self, surface:pygame.Surface, pos:tuple, size:tuple): # Nathan
        # La taille et la position correspondent à une bande au milieu de l'écran
        if self.chest_display is None:
            self.chest_display = ChestDisplay(surface, pos, size) # Initier un objet ChestDisplay dans self.chest_display
            self.chest_display.closed = False # L'ouvrir
        self.chest_display.display()

    def display_item_choice(self, game, pos: tuple, size: tuple): # Hugo avec l'aide de Nathan
        """
        Affiche un objet aléatoire dans une carte, propose au joueur de l'accepter ou de le refuser.
        """
        self.game = game
        # Création d'un objet aléatoire
        if self.item is None:
            type_objet = self.get()
            nom = type_objet.capitalize()

            if type_objet == "arme":
                nom = choice(["Lance", "Epée"])

            soin, degat, resistance = get_random_item_stats(game, type_objet)

            self.item = Objet(nom, type_objet, soin=soin, degat=degat, resistance=resistance)

        if self.item_display is None:
            self.item_display = ItemDisplay(game.screen, pos, (size[0], size[1]/2), self.item)
        if self.text_display is None:
            val = is_better(self.item, game.personnage.inventaire.get(self.item.type))
            if val < 0:
                color = (255, 0, 0)
            elif val > 0:
                color = (0, 255, 0)
            else:
                color = (0, 0, 0)
            self.text_display = TextDisplay(self.item.get_message(), game.screen, game.clock, size = (size[0], size[1]/2), pos=(pos[0], pos[1] + size[1]/2), background_color=(50, 50, 50), color=color)

        self.item_display.display()
        self.text_display.display()

        actions = [
            ("Accepter", self.accept_item),
            ("Refuser", self.decline_item)
        ]
        buttons_surface = pygame.Surface((size[0], 80), pygame.SRCALPHA)
        buttons_surface.fill((0, 0, 0, 150))
        buttons_pos = (pos[0], pos[1] + size[1] + 10)

        self.buttons = make_buttons(buttons_surface, actions, space_percent=20, button_bloc_pos=buttons_pos)

        # Affichage des boutons
        for b in self.buttons:
            b.display()

        game.screen.blit(buttons_surface, buttons_pos)

    def buttons_event(self, event): # Nathan
        if self.buttons is None:
            return

        for button in self.buttons:
            button.handle_event(event)

    def accept_item(self): # Nathan
        """
        Ajoute l'item au joueur, puis marque la fin de l'action.
        """
        if hasattr(self, "item") and self.item:
            self.game.personnage.inventaire.add(self.item)
            self.game.personnage.reset()
            self.game.current_texts.append(
                TextDisplay(f"Vous obtenez : {self.item.get_message()}", self.game.screen, self.game.clock)
            )

        self.actions_end = True
        self.end = True

    def decline_item(self): # Nathan
        """
        Le joueur refuse l’objet, simplement fermer l’interface du coffre.
        """
        self.actions_end = True
        self.end = True

    def reset(self): # Nathan
        self.chest_display = None
        self.end = False
        self.actions_end = False
        self.item = None
        self.item_display = None
        self.text_display = None