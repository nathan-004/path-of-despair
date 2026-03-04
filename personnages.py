from random import randint, uniform

from items import Inventaire, Objet
from display import *
from constants import *
from son import *

class Personnage: # Lino
    def __init__(self, nom, pv, degats, resistance):
        """
        Constructeur de la classe Personnage
        Attributs :
            - nom : chaine de caractères qui sert de prénom au personnage
            - pv : entier positif ou nul qui représente les point de vie du personnage
            - degats : entier positif qui agit comme quantité de degats qu'inflige le personnage
            - resistance : entier soustrayant les degats subit pour connaitre le nombre de point de vie retirée
            
            - pv_base : entier positif représentant les points de vie max des personnages, il sert à calculer les pv restants 
            - degats_base : entier représentant la statistique de dégats des personnage, il sert à calculer les dégats restants après qu'il soit soustrait a la résistance   
            - resistance_base : entier représentant la statistique de résistance des personnage, il sert à calculer les dégats subit après avoir soustrait les dégats          
            
            - exp : quantité d'expérience des personnage représenté par des nombres décimals
            - level: entier signifiant le niveau des personnages
            - inventaire : objet
        """
        self.nom = nom
        self.pv = pv
        self.degat = degats
        self.resistance = resistance

        self.pv_base = self.pv
        self.degat_base = self.degat
        self.resistance_base = self.resistance

        self.exp = 0
        self.level = 0
        self.inventaire = Inventaire()

    def use(self, obj:Objet):
        potion_use() if obj.soin > 0 else None
        return obj.use(self)

    def degat_subit(self, degats):
        """
        calcul les dégats subit en les soustrayant a la résistance du personnage qui les subits 
        """
        degat_restant = degats - (degats * self.resistance)
        self.pv = self.pv - degat_restant

        if self.pv < 0:
            self.pv = 0

        return degat_restant

    def attaque(self, ennemi):
        """
        attaque lancé par le personnage ayant une faible chance d'échec, sa puissance se base sur les dégats de celui-ci
        """
        a = randint(1, 10)
        if a >= 1:
            if self.nom=="Ventre d'Acier":
                heavy_attack()
            else:
                attack_sword()
            return ennemi.degat_subit(self.degat)
        else:
            miss_attack()
            return None

    def attaque_lourde(self, ennemi):
        """
        attaque plus puissante multipliant par 2 les dégats du personnage mais elle possède une grande chance d'échouer  
        """ 
        a = randint(1, 10)
        if a >= 7:
            heavy_attack()
            return ennemi.degat_subit(self.degat*2)
        else:
            miss_attack()
            return None

    def level_up(self):
        """Prend les attributs du personnage de base et ajoute un nombre * level"""
        if self.level >= MAX_LEVEL:
            self.level = MAX_LEVEL - 1
        self.level = self.level + 1

    def get_max_pv(self):
        return self.pv_base + PLAYER_LEVEL_AUGMENTATION_PV * self.level

    def get_stats_message(self) -> str:
        content = f"{self.nom} & PV : {self.pv}/{self.get_max_pv()} & Degats : {self.degat} & Resistance : {self.resistance} & Exp : {self.exp}/{ BASE_EXP_LEVEL_UP * (BASE_EXP_LEVEL_UP_AUGMENTATION_COEFF**self.level)} & Level : {self.level}"
        return content

class Monstre(Personnage): # Lino
    """"""
    def __init__(self, nom, pv=uniform(-MONSTER_BASE_PV_RANGE/2, MONSTER_BASE_PV_RANGE/2) + MONSTER_BASE_PV, degats=uniform(-MONSTER_BASE_ATTACK_RANGE/2, MONSTER_BASE_ATTACK_RANGE/2) + MONSTER_BASE_ATTACK, resistance=uniform(-MONSTER_BASE_RESISTANCE_RANGE/2, MONSTER_BASE_RESISTANCE_RANGE/2) + MONSTER_BASE_RESISTANCE):
        super().__init__(nom, pv, degats, resistance)
        self.ennemi_display = None
        self.health_bar = None
        self.damage = False

    def level_up(self, level:int = None):
        if level is None:
            super().level_up()
        else:
            self.level = level

        self.pv = self.pv_base + MONSTER_LEVEL_AUGMENTATION_PV * self.level
        self.degat = self.degat_base + MONSTER_LEVEL_AUGMENTATION_ATTACK * self.level
        self.resistance = min(self.resistance_base + MONSTER_LEVEL_AUGMENTATION_RESISTANCE * self.level, MAX_MONSTER_RESISTANCE)

    def degat_subit(self, degats):
        self.damage = True
        monster_damage()
        return super().degat_subit(degats)

    def display(self, surface:pygame.Surface): # Abel
        if self.ennemi_display is None:
            self.ennemi_display = EnnemiDisplay(surface, (get_size(surface, 40), 125), 0.5, MONSTERS[self.nom]["image"])
            self.health_bar = HealthBar(self, (get_size(surface, 40), get_size(surface, 5, "height")), (get_size(surface, 20), 50), surface)
        if self.damage:
            self.ennemi_display.display_damage()
        else:
            self.ennemi_display.display()
        self.health_bar.display()
        self.damage = False

    def use(self, obj:Objet):
        self.pv += obj.soin
        potion_use() if obj.soin > 0 else None
        self.degat += obj.degat
        self.resistance += obj.resistance

class Joueur(Personnage): # Lino
    def __init__(self, nom, pv, degats, resistance, position:tuple, inventaire:Inventaire = None, game = None):
        super().__init__(nom, pv, degats, resistance)
        self.position = position
        self.direction = (1, 0) # Direction de base vers la droite
        if inventaire is None:
            inventaire = Inventaire()
        self.inventaire = inventaire
        self.game = game

    def equipe_obj(self, obj:Objet):
        self.obj = obj

    def move(self, direction:tuple):
        open_door()
        self.position = (self.position[0] + direction[0], self.position[1] + direction[1])
        self.direction = direction

    def victoire(self, ennemi:Personnage):
        """Ajoute de l'exp au personnage en fonction du niveau de l'ennemi"""
        new_exp = BASE_EXP_REWARD * (BASE_EXP_LEVEL_UP_AUGMENTATION_COEFF ** ennemi.level) + randint(-BASE_EXP_REWARD_RANGE//2, BASE_EXP_REWARD_RANGE//2)
        self.exp += new_exp
        self.game.current_texts.append(TextDisplay(f"Vous avez battu {ennemi.nom} vous gagnez {new_exp} exp", self.game.screen, self.game.clock))

        val = BASE_EXP_LEVEL_UP * (BASE_EXP_LEVEL_UP_AUGMENTATION_COEFF**self.level)
        while self.exp >= val:
            if self.exp >= val:
                self.level_up()
                self.exp -= val
                val *= BASE_EXP_LEVEL_UP_AUGMENTATION_COEFF

    def level_up(self):
        super().level_up()
        self.reset()
        self.game.current_texts.append(TextDisplay(f"Vous passez au niveau {self.level}", self.game.screen, self.game.clock))

    def reset(self):
        self.pv = self.pv_base + PLAYER_LEVEL_AUGMENTATION_PV * self.level
        self.degat = self.degat_base + PLAYER_LEVEL_AUGMENTATION_ATTACK * self.level
        self.resistance = self.resistance_base + PLAYER_LEVEL_AUGMENTATION_RESISTANCE * self.level
        self.inventaire.equip(self)
        self.resistance = min(self.resistance, MAX_PLAYER_RESISTANCE)
        self.pv, self.degat, self.resistance = round(self.pv, 1), round(self.degat, 1), round(self.resistance, 3)

    def get_content(self) -> dict:
        """Renvoie les informations sous forme de dictionnaire qui pourront être transcrite au format json"""
        content = {
            "position": self.position,
            "inventaire": self.inventaire.get_content(),
            "level": self.level,
            "exp": self.exp
        }

        return content

    def load(self, content:dict):
        """Modifie self.personnage pour correspondre aux valeurs de content"""
        self.position = tuple(content["position"])
        self.level = content["level"]
        self.exp = content["exp"]
        self.inventaire.load(content["inventaire"])
        self.reset()