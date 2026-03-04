import pygame
import time
from random import shuffle, randint, choice, uniform
import json
from typing import Optional

from display import *
from son import *

from map import create_one_solution_map, get_absolute_direction, Map
from personnages import *
from items import *

from constants import *

BUTTONS = []

def add_random_dialogue(monster_type:str, event:str, game): # Nathan
    """
    Créé un dialogue aléatoire en fonction du type de monstre, de l'évènement et de la classe `Game`
    
    Parameters
    ----------
    monster_type:str
        Type de monstre -> 'Ventre d'acier', 'Chevalier'
    event:str
        Evènements -> degats reçus, mort du joueur/monstre, début du combat, ...
    game:Game
        Contient les informations de la partie en cours
    """
    if monster_type == "Ventre d'Acier":
        if event == "start" or event == "monster_death" or event == "player_death":
            for el in MONSTERS[monster_type]["dialogues"][event]:
                game.current_texts.append(get_dialogue_text(el, None, game.screen, game.clock))
            return
        elif event == "receive_damage":
            gen = MONSTERS[monster_type]["dialogues"][event]
            txts = next(gen, ("...",))
            for el in txts:
                game.current_texts.append(get_dialogue_text(el, None, game.screen, game.clock))
            return
        else:
            pass

    txt = get_random_dialogue(monster_type, event)

    if txt is not None:
        game.current_texts.append(get_dialogue_text(txt, None, game.screen, game.clock))

def get_random_dialogue(monster_type:str, event:str) -> Optional[str]: # Nathan
    """
    Créé un dialogue aléatoire en fonction du type de monstre, de l'évènement et de la classe `Game`
    
    Parameters
    ----------
    monster_type:str
        Type de monstre -> 'Ventre d'acier', 'Chevalier'
    event:str
        Evènements -> degats reçus, mort du joueur/monstre, début du combat, ...
    """
    # Sur 10, seulement 5 fois où il y a du texte
    max_ = 10
    prob = 5
    try:
        texts = MONSTERS[monster_type]["dialogues"][event]
    except:
        return "..."

    if randint(1, max_) <= prob:
        return choice(texts)
    return None

def get_random_monster(game): # Nathan
    """
    Renvoie un monstre aléatoire en fonction de la map où se situe le joueur
    Si la map est celle de base, calcule les statistiques en fonction du niveau et de la position du joueur
    """
    if game.map.name == "start":
        return Monstre("Mannequin d'entraînement", 30, 0, 0)
    elif game.map.name == "end":
        max_player_pv = game.personnage.get_max_pv()
        return Monstre("Ventre d'Acier", max_player_pv * 2.5, max_player_pv / 3, 0.75)

    monster_type = choice(MONSTERS_LIST)
    monster = Monstre(monster_type)
    monster.level_up(get_level(game))
    return monster

class Game: # Nathan
    def __init__(self):
        self.height, self.width = 15, 16
        self.elements = self.get_maps()
        self.map, self.texts = next(self.elements)
        self.personnage = Joueur("Nom", PLAYER_BASE_PV, PLAYER_BASE_ATTACK, PLAYER_BASE_RESISTANCE, self.map.get_start_position(), game = self)

        self.visited = set()
        self.last_moved = False
        self.end = False

    def display_room(self,screen:pygame.Surface, percentage=70): # Abel
        """Affiche la Salle et les portes en fonction des directions où il est possible de se diriger"""
        if self.room is None:
            self.room = RoomDisplay(screen, percentage)
        if self.last_moved:
            self.room.start_enter()
            self.last_moved = False
        doorL =  pygame.image.load('assets\\images\\doors\\Porte_cote.png')#.transform.flip(img, True, False)
        doorC =  pygame.image.load('assets\\images\\doors\\Porte_Face.png')
        doorR =  pygame.image.load('assets\\images\\doors\\Porte_cote.png')
        doors = [doorR, doorL, doorC]
        dir_ = [(-1, 0), (1, 0), (0, -1)]
        self.room.display_bg()
        for  i in range(3):
            direction = get_absolute_direction(self.personnage.direction, dir_[i])
            if self.map.can_move(self.personnage.position, direction):
                doors[i] = pygame.transform.scale(doors[i], (get_size(screen, 13*(percentage/100)), get_size(screen, 71*(percentage/100), "height"))) if i != 2 else pygame.transform.scale(doors[i], (get_size(screen,(300*100/get_size(screen,100))*(percentage/100)), get_size(screen, 49*(percentage/100), "height")))
                doors[i] = pygame.transform.flip(doors[i], True, False) if i == 0 else doors[i]
                screen.blit(doors[i],(get_size(screen, ((99.7-percentage)/2)+((85/(100/percentage))if i == 1 else (4/(100/percentage))) ),get_size(screen, 26*(percentage/99.7), "height"))) if i != 2 else screen.blit(doors[i],(get_size(screen, ((100-percentage)/2)+((36.3-(10/(100/percentage)))) ),get_size(screen, 32*(percentage/99.7), "height")))
        self.room.display_shade()
        self.room.display_enter()

    def start_menu(self):
        """
        Affiche le menu de départ qui contient les boutons pour charger, réanitialiser, ou quitter une partie
        Permet aussi de lancer la démo
        """
        pygame.font.init()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

        buttons = [("Charger", self._start_loaded_game), ("Nouvelle", self._start_new_game), ("Demo", self._start_demo_game), ("Quitter", self._quit_start_menu)] # A modifier pour stopper l'erreur
        buttons_size = (get_size(screen, 50), get_size(screen, 75, "height"))
        buttons_pos = (get_size(screen, 25), get_size(screen, 12.5, "height"))
        buttons_surface = pygame.Surface(buttons_size, pygame.SRCALPHA)
        buttons = make_vertical_buttons(buttons_surface, buttons, 10, buttons_pos)

        self.start_running = True

        while self.start_running: # Créer la boucle de fonctionnement
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.start_running = False

                for button in buttons:
                    button.handle_event(event)

            for button in buttons:
                button.display()

            screen.fill((0,0,0))
            screen.blit(buttons_surface, buttons_pos)
            pygame.display.flip()

        pygame.quit()

    def main(self):
        """
        Lance la boucle principale du jeu.
        Gère l'affichage et la logique du jeu
        """
        start_main = time.time()
        print(f"{start_main}s - Départ Main")
        pygame.font.init()
        MUSIQUE = True
        try:
            print(f"{time.time() - start_main}s - Départ musique mixer init")
            pygame.mixer.init()
        except pygame.error as e:
            print(RED, "Erreur lors de l'initialisation du son (vérifier si sortie audio connectée) :", e, RESET)
            MUSIQUE = False
            print(f"{time.time() - start_main}s - Réception erreur musique")
        
        print(f"{time.time() - start_main}s - Initialisation Musique")

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        map_size = (get_size(self.screen, 30, "height"), get_size(self.screen, 30, "height"))
        map_surface = pygame.Surface((self.map.width * 1, self.map.height * 1), pygame.SRCALPHA)
        map_surface = resize(map_surface, map_size)
        map_surface.fill((0, 0, 0, 180))
        map_position = (get_size(self.screen, 100) - map_size[0], get_size(self.screen, 100, "height") - map_size[1])

        buttons_size = (get_size(self.screen, 100), 50)
        buttons_surface = pygame.Surface(buttons_size, pygame.SRCALPHA)
        buttons_surface.fill((0, 0, 0, 180))
        buttons_position = (0, get_size(self.screen, 100, "height") - buttons_size[1])

        player_health_bar = HealthBar(self.personnage, (0, 0), (150, 50), self.screen)

        item_choice_size = (get_size(self.screen, 40), get_size(self.screen, 40, "height"))
        item_choice_pos = (get_size(self.screen, 30), get_size(self.screen, 30, "height"))
        self.coffre = Coffre(1)
        
        print(f"{time.time() - start_main}s - Initialisation Affichage + map")

        self.combat = False
        self.clock = pygame.time.Clock()
        self.room = None

        debug_text_size = (75, 50)
        debug_text_pos = (get_size(self.screen, (100 - debug_text_size[0])/2), get_size(self.screen, (100 - debug_text_size[1])/2, "height"))
        debug_text_size = (get_size(self.screen, debug_text_size[0]), get_size(self.screen, debug_text_size[1], "height"))
        debug_text = TextDisplay(self.personnage.get_stats_message(), self.screen, self.clock, background_color=(0,0,0), color=(255,255,255), pos=debug_text_pos, size=debug_text_size)
        
        print(f"{time.time() - start_main}s - Initialisation texte")
        
        if MUSIQUE:
            self.musique = Musique("assets/sound/musique_boucle1.mp3")

        self.current_texts = []
        
        print(f"{time.time() - start_main}s - Fin initialisation attributs")

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                    if self.current_texts != []:
                        if any(pygame.key.get_pressed()):
                            if self.current_texts != []:
                                if self.current_texts[0].end:
                                    self.current_texts.pop(0)
                                else:
                                    self.current_texts[0].frames = len(self.current_texts[0].txt)
                        continue

                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.move((1, 0))
                    elif event.key == pygame.K_UP or event.key == INPUT_LIST[0]:
                        self.move((0, -1))
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self.move((0, 1))
                    elif event.key == pygame.K_LEFT or event.key == INPUT_LIST[1]:
                        self.move((-1, 0))
                    elif any(pygame.key.get_pressed()):
                        if self.current_texts != []:
                            if self.current_texts[0].end:
                                self.current_texts.pop(0)
                            else:
                                self.current_texts[0].frames = len(self.current_texts[0].txt)

                if self.combat:
                    self.combat.buttons_event(event)
                if self.coffre:
                    self.coffre.buttons_event(event)

            if MUSIQUE:
                self.musique.play_music(True)

            if self.end:
                self.end.display()
                if self.end.end:
                    self.end = False
                    running = False
                pygame.display.flip()
                self.clock.tick(60)
                continue

            if self.personnage.position in self.texts and self.personnage.position not in self.visited:
                for text in self.texts[self.personnage.position]:
                    self.current_texts.append(TextDisplay(f"- {text}", self.screen, self.clock))
            if self.personnage.position in self.texts and not self.combat:
                self.save()

            cur_room = self.map.grid[self.personnage.position[1]][self.personnage.position[0]]

            if cur_room.type == "end" and not cur_room.locked:
                try:
                    self.map, self.texts = next(self.elements)
                    self.personnage.position = self.map.get_start_position()
                    map_surface = pygame.Surface((self.map.width * 1, self.map.height * 1), pygame.SRCALPHA)
                    map_surface = resize(map_surface, map_size)
                    map_surface.fill((0, 0, 0, 180))
                    self.visited = set()
                    continue
                except StopIteration:
                    if self.current_texts == []:
                        self.end = Credits(CREDITS_TEXT, self.screen, self.clock,5)

            self.display_room(self.screen)
            self.map.draw(surface=map_surface, player = self.personnage)
            self.screen.blit(map_surface, map_position)

            if self.combat:
                if self.combat.ennemi.nom == "Ventre d'Acier":
                    if MUSIQUE:
                        self.musique.music_change("assets/sound/musique_boss.mp3") if self.musique.path != "assets/sound/musique_boss.mp3" else None
                if self.combat.is_ended() and self.current_texts == []:
                    if type(self.combat.winner) is Joueur:
                        self.combat = False
                        cur_room.monster = False
                        if MUSIQUE:
                            self.musique.music_change("assets/sound/musique_boucle1.mp3") if self.musique.path != "assets/sound/musique_boucle1.mp3" else None
                        continue
                    else:
                        running = False
                if self.combat.tour % 2 != 0:
                    self.combat.ennemi_turn()
                self.combat.display_buttons(buttons_surface, button_bloc_pos=buttons_position)
                self.screen.blit(buttons_surface, buttons_position)
                self.combat.ennemi.display(self.screen)
            elif cur_room.type == "key":
                self.map.open()
                cur_room.type = "path"
                key_open()
                self.current_texts.append(TextDisplay("Vous avez trouvé une clé", self.screen, self.clock))
                self.current_texts.append(TextDisplay("Une porte s'est ouverte ...", self.screen, self.clock))
            elif cur_room.chest:
                if not self.combat and not self.room.enter_animation:
                    if self.coffre.chest_display is None and not self.coffre.end:
                        self.current_texts.append(TextDisplay("Vous trouvez un coffre. Vous l'ouvrez.", self.screen, self.clock))
                    if self.current_texts != [] and (self.coffre.chest_display is None or not self.coffre.chest_display.ended):
                        self.coffre.reset()
                    self.coffre.display(self, item_choice_pos, item_choice_size)
                    if self.coffre.end:
                        cur_room.chest = False
                        self.save()
                        self.coffre.reset()

            if cur_room.monster:
                if not self.combat and not self.room.enter_animation:
                    self.combat = Combat(self.personnage, get_random_monster(self), self)
                    self.current_texts.append(TextDisplay(f"Vous tombez nez à nez avec {self.combat.ennemi.nom} LV{self.combat.ennemi.level}", self.screen, self.clock))
                    add_random_dialogue(self.combat.ennemi.nom, "start", self)

            player_health_bar.display()

            if self.current_texts != []:
                self.current_texts[0].display()

            self.visited.add(self.personnage.position)

            keys = pygame.key.get_pressed()

            if keys[pygame.K_e]:
                stats = self.personnage.get_stats_message()
                if f"*{stats}*" != debug_text.txt:
                    debug_text = TextDisplay(stats, self.screen, self.clock, background_color=(0, 0, 0), color=(255,255,255), pos=debug_text_pos, size=debug_text_size)
                borders = pygame.Rect(debug_text_pos, debug_text_size)
                debug_text.display(20)
                pygame.draw.rect(self.screen, (255,255,255) , borders, 2)

            pygame.display.flip()
            self.clock.tick(100)

    def move(self, direction:tuple):
        direction = get_absolute_direction(self.personnage.direction, direction)
        if self.map.can_move(self.personnage.position, direction):
            if not self.combat:
                self.personnage.move(direction)
                self.last_moved = True
            else:
                self.current_texts.append(TextDisplay("Ne vous en allez pas si vite !", self.screen, self.clock))
        Objet.current_room = self.personnage.position

    def get_maps(self, demo=False):
        """Renvoie un générateur contenant un tuple map, text"""
        yield (self._load_map("assets/maps/start"), self._load_text("assets/maps/start"))
        if not demo:
            base_text = {
                (0, self.height//2): ["Vous y êtes arrivé !", "Il ne vous reste plus qu'à trouver le chemin dans ce donjon, à battre tous les ennemis sur votre chemin, à acquérir les meilleurs statistiques.", "On ne sait jamais, ce qui semble être la fin peut parfois n'être que le début d'une plus grande aventure."],
                (self.width//4, self.height//2): ["Vous avez l'air de bien vous en sortir", "En espérant que vous ne mourriez pas dans d'atroces souffrances.", "Un homme comme vous a déjà fait son apparition auparavant ..."],
                (self.width//4 + 1, self.height // 2): ["Il était rempli d'espoir, il s'en est sorti pendant bien longtemps.", "Trop longtemps", "Si longtemps qu'il en a perdu la raison."],
                (self.width//2, self.height // 2): ["Chaque monstre connaît son armure iconique. & Ils ont tous appris à la fuir", "Car lassé de cet endroit, il n'a laissé aucun témoin de son passage."],
                (self.width//2 + 1, self.height // 2): ["Seulement un nom, une réputation, et les corps qu'il a laissé derrière lui.", "Mais n'importe qui deviendrait fou dans cet endroit. Non ?"],
                (self.width - self.width//4, self.height//2): ["On dit de lui qu'il a finalement réussi à sortir de cet endroit.", "Et qu'il attend patiemment tout survivant pour ...", "On s'est compris & Comme ça il enlève le poids de ce traumatisme de leurs épaules, littéralement ..."],
                (self.width - 1, self.height//2): ["Tu as finalement réussi à franchir tous ces obstacles.", "Tu y es ! La sortie est devant tes yeux !", "Ta détermination a payé.", "Mais à quel prix ................."]
            }
            yield (create_one_solution_map(self.width, self.height, 4), base_text)
        else:
            yield (self._load_map("assets/maps/demo"), self._load_text("assets/maps/demo"))
        yield (self._load_map("assets/maps/end"), self._load_text("assets/maps/end"))

    def _load_map(self, filename:str) -> Map:
        """Renvoie la Map à partir du fichier donné"""
        map = Map(0,0)
        map.load(filename)
        map.name = filename.split("/")[-1] if "/" in filename else filename
        return map

    def _load_text(self, filename:str) -> dict:
        """Renvoie le dictionnaire sous la forme {pos: ['text1']}"""
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        text = json.loads(content)["texts"]

        def decode_tuple(s) -> tuple:
            return tuple(int(el) for el in s.split(","))

        res = {}
        for key, value in text.items():
            res[decode_tuple(key)] = value
        return res

    def save(self, filename:str = "assets/saves/save1"):
        # Sauvegarder la map
        map_content = self.map.get_content()
        personnage_content = self.personnage.get_content()
        result = {
            "map": map_content,
            "player": personnage_content,
            "visited": list(self.visited)
        }

        with open(filename, "w") as f:
            json.dump(result, f, indent=4)

    def load(self, filename:str = "assets/saves/save1"):
        """
        Gère le chargement d'une partie depuis une sauvegarde
        """
        with open(filename, "r") as f:
            content = json.load(f)

        self.elements = self.get_maps()
        self.map, self.texts = next(self.elements)
        self.visited = set([tuple(pos_list) for pos_list in content["visited"]])
        map_name = content["map"].get("name", None)
        if map_name is None or map_name == "end" or map_name == "demo":
            self.map, self.texts = next(self.elements)
        if map_name == "end":
            self.map, self.texts = next(self.elements)
        self.map.load_matrice_format(content["map"]["grid"])
        self.personnage.load(content["player"])

    def _start_loaded_game(self):
        try:
            self.load()
        except Exception:
            print(f"{RED}Erreur lors du chargement de la map{RESET}")
            print(f"{GREEN}Création d'une nouvelle map ...{RESET}")
            self._start_new_game()
            return
        self.main()

    def _start_new_game(self):
        self.elements = self.get_maps()
        self.map, self.texts = next(self.elements)
        self.personnage.__init__('nom', PLAYER_BASE_PV, PLAYER_BASE_ATTACK, PLAYER_BASE_RESISTANCE, self.map.get_start_position(), game = self)
        self.main()

    def _start_demo_game(self):
        start_time = time.time()
        self.elements = self.get_maps(True)
        print(f"{time.time() - start_time}s - Récupération des maps")
        self.map, self.texts = next(self.elements)
        print(f"{time.time() - start_time}s - Définition des maps")
        self.personnage.__init__('nom', PLAYER_BASE_PV, PLAYER_BASE_ATTACK, PLAYER_BASE_RESISTANCE, self.map.get_start_position(), game = self)
        print(time.time())
        self.main()

    def _quit_start_menu(self):
        self.start_running = False

class Combat: # Lino
    def __init__(self, joueur:Joueur, ennemi:Personnage, game: Game):
        self.joueur = joueur
        self.ennemi = ennemi
        self.tour = 0 # Pair quand c'est au tour du joueur
        self.buttons = None
        self.game = game
        self.winner = None

    def joueur_utiliser(self):
        """Fait utiliser le seul consommable de l'inventaire du joueur"""
        if self.tour % 2 == 0:
            try:
                objet = list(self.joueur.inventaire.consommables.values())[0]
                if not self.joueur.use(objet):
                    self.game.current_texts.append(TextDisplay("Cet objet a déjà été utilisé.", self.game.screen, self.game.clock))
                else:
                    self.game.current_texts.append(TextDisplay(f"Vous utilisez l'objet : {objet.get_message()}", self.game.screen, self.game.clock))
            except IndexError:
                self.game.current_texts.append(TextDisplay("Vous ne possédez pas de consommables ...", self.game.screen, self.game.clock))
        else:
            return
        self.tour += 1

    def joueur_attaque(self):
        """Attaque du joueur sur l'ennemi"""
        if self.tour % 2 == 0:
            att = self.joueur.attaque(self.ennemi)
            if att is None:
                self.game.current_texts.append(TextDisplay(f"Vous avez stressé et vous avez manqué votre attaque ...", self.game.screen, self.game.clock))
                add_random_dialogue(self.ennemi.nom, "miss_attack", self.game)
            else:
                self.game.current_texts.append(TextDisplay(f"Vous infligez {att:.1f} dégâts {NEW_LINE_CHARACTER} Il ne lui reste plus que {self.ennemi.pv:.1f} pv", self.game.screen, self.game.clock))
            if self.ennemi.pv > 0 and not att is None:
                add_random_dialogue(self.ennemi.nom, "receive_damage", self.game)
        else:
            return

        self.tour += 1

    def joueur_attaque_lourde(self):
        """Attaque lourde du joueur"""
        if self.tour % 2 == 0:
            att = self.joueur.attaque_lourde(self.ennemi)
            if att is None:
                self.game.current_texts.append(TextDisplay(f"Vous avez tout risqué mais vous êtes loupé ...", self.game.screen, self.game.clock))
                add_random_dialogue(self.ennemi.nom, "miss_attack", self.game)
            else:
                self.game.current_texts.append(TextDisplay(f"Vous infligez {att:.1f} dégâts {NEW_LINE_CHARACTER} Il ne lui reste plus que {self.ennemi.pv:.1f} pv", self.game.screen, self.game.clock))
            if self.ennemi.pv > 0 and not att is None:
                add_random_dialogue(self.ennemi.nom, "receive_damage", self.game)
        else:
            return

        self.tour += 1

    def is_ended(self) -> bool:
        """Renvoie si le combat est terminé et modifie self.winner par le vainqueur"""
        if self.winner != None:
            return True
        if not any([pers.pv <= 0 for pers in [self.ennemi, self.joueur]]):
            return False
        self.winner = self.joueur if self.ennemi.pv <= 0 else self.ennemi
        other = self.ennemi if self.ennemi.pv <= 0 else self.joueur

        if type(self.winner) is Joueur:
            self.winner.victoire(other)
            add_random_dialogue(self.ennemi.nom, "monster_death", self.game)
        else:
            self.game.current_texts.append(TextDisplay(f"Vous êtes morts ...", self.game.screen, self.game.clock))
            add_random_dialogue(self.ennemi.nom, "player_death", self.game)

        return True

    def ennemi_turn(self):
        """Tour de l'ennemi choisir action ennemi"""
        if self.tour % 2 == 0 or self.game.current_texts != []:
            return
        a = randint(1,10)

        if self.ennemi.pv <= self.ennemi.pv_base * 0.5: # Jouer ici
            if self.game.personnage.pv < self.ennemi.damage:
                deg = self.ennemi.attaque(self.joueur)
                self.game.current_texts.append(TextDisplay(f"Il vous inflige {deg:.1f} dégâts {NEW_LINE_CHARACTER} Il ne vous reste plus que {self.joueur.pv:.1f} pv", self.game.screen, self.game.clock))
            elif a <=3:
                obj = Objet("Potion de soin contenant du vice", "potion", soin=MONSTER_BASE_ITEM_SOIN)
                self.ennemi.use(obj)
                self.game.current_texts.append(TextDisplay(f"L'ennemi utilise l'objet : {NEW_LINE_CHARACTER} {obj.get_message()}", self.game.screen, self.game.clock))
            else:
                deg = self.ennemi.attaque(self.joueur)
                self.game.current_texts.append(TextDisplay(f"Il vous inflige {deg:.1f} dégâts {NEW_LINE_CHARACTER} Il ne vous reste plus que {self.joueur.pv:.1f} pv", self.game.screen, self.game.clock))

        elif self.ennemi.pv <= self.ennemi.pv_base * 0.25:
            if self.game.personnage.pv < self.ennemi.damage:
                deg = self.ennemi.attaque(self.joueur)
                self.game.current_texts.append(TextDisplay(f"Il vous inflige {deg:.1f} dégâts {NEW_LINE_CHARACTER} Il ne vous reste plus que {self.joueur.pv:.1f} pv", self.game.screen, self.game.clock))
            elif a <=5:
                obj = Objet("Potion de soin contenant du vice", "potion", soin=MONSTER_BASE_ITEM_SOIN)
                self.ennemi.use(obj)
                self.game.current_texts.append(TextDisplay(f"L'ennemi utilise l'objet : {NEW_LINE_CHARACTER} {obj.get_message()}", self.game.screen, self.game.clock))
            else:
                deg = self.ennemi.attaque(self.joueur)
                self.game.current_texts.append(TextDisplay(f"Il vous inflige {deg:.1f} dégâts {NEW_LINE_CHARACTER} Il ne vous reste plus que {self.joueur.pv:.1f} pv", self.game.screen, self.game.clock))

        else:
            deg = self.ennemi.attaque(self.joueur)
            self.game.current_texts.append(TextDisplay(f"Il vous inflige {deg:.1f} dégâts {NEW_LINE_CHARACTER} Il ne vous reste plus que {self.joueur.pv:.1f} pv", self.game.screen, self.game.clock))
        self.tour += 1

    def display_buttons(self, surface:pygame.Surface, space_percent:int = 20, button_bloc_pos:tuple = (0, 0)): # Nathan
        """
        Initie les boutons de combat
        """
        surface.fill((0, 0, 0, 180))

        if self.game.current_texts != []:
            return

        if self.buttons is None:
            buttons = [("ATTAQUE", self.joueur_attaque), ("TOUT RISQUER", self.joueur_attaque_lourde), ("UTILISER", self.joueur_utiliser)]
            self.buttons = make_buttons(surface, buttons, space_percent, button_bloc_pos)

        if self.tour % 2 == 0:
            for button in self.buttons:
                button.display()

    def buttons_event(self, event): # Nathan
        if self.game.current_texts != []:
            return
        if self.buttons is None or self.tour % 2 != 0:
            return

        for button in self.buttons:
            button.handle_event(event)

if __name__ == "__main__":
    g = Game()
    g.start_menu()
