import random
import copy
import sys
import socket
from MainWindow import *
from PyQt5.QtGui import QPainter, QPolygon, QColor, QBrush, QPen
from PyQt5.QtCore import QPoint, Qt, QRectF, QTimer
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsItem

import xml.etree.ElementTree as ET
import json

HOST = "localhost"
PORT = 5555


number_of_players = 2
candy_colors = [31, 32, 33, 34, 35, 36, 37, 30]
number_of_types = 7
candy_colors_gui = [QColor(100, 0, 0), QColor(0, 100, 0), QColor(0, 0, 100), QColor(100, 100, 0),
                    QColor(100, 0, 100), QColor(0, 100, 100), QColor(100, 50, 0), QColor(100, 100, 100)]


def copy_candy(candy_1, candy_2):
    """
    Skopiowanie parametrow cukierka
    :param candy_1: cukierek docelowy
    :param candy_2: cukierek kopiowany
    :return: None
    """
    candy_1.candy_type = candy_2.candy_type
    candy_1.y = candy_2.y
    candy_1.x = candy_2.x


class Candy(QGraphicsItem):
    number_of_types = 7
    def __init__(self, candy_type, y=0, x=0):

        super().__init__()
        if candy_type < 0:
            self.candy_type = random.randrange(0, self.number_of_types)
        else:
            self.candy_type = candy_type

        self.y = y
        self.x = x
        self.agent_pos = False  # Czy cukierek jest aktualna pozycja agenta

    def boundingRect(self):
        """
        Metoda okreslajaca bounding Rectangle danego pola (cukierka)
        Konieczna do zdefiniowania abstrakcyjana metoda z QGraphicsItem,
        uzywana przy aktualizacji wyswietlania
        :return: boundingRect
        """
        bias_x_1 = 50
        bias_y_1 = 20
        i = self.x - 14
        j = self.y - 9

        parity_ind = self.y % 2
        side_size = 10

        return QRectF(bias_x_1 + int((i*1.732 + parity_ind*0.866 + 0) * side_size), bias_y_1 + int((j * 1.5 + 0) * side_size),
                      side_size*0.866*2, side_size*2)

    def paint(self, painter, option, widget):
        """
        Metoda rysujaca cukierek, konieczna do zdefiniowania abstrakcyjana metoda z QGraphicsItem
        :param painter:
        :param option:
        :param widget:
        :return: None
        """
        bias_x_1 = 50
        bias_y_1 = 20
        i = self.x - 14
        j = self.y - 9

        parity_ind = self.y % 2

        side_size = 10
        points = QPolygon([
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 0) * side_size),
                   bias_y_1 + int((j * 1.5 + 0.5) * side_size)),
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 0) * side_size),
                   bias_y_1 + int((j * 1.5 + 1.5) * side_size)),
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 0.866) * side_size),
                   bias_y_1 + int((j * 1.5 + 2) * side_size)),
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 1.732) * side_size),
                   bias_y_1 + int((j * 1.5 + 1.5) * side_size)),
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 1.732) * side_size),
                   bias_y_1 + int((j * 1.5 + 0.5) * side_size)),
            QPoint(bias_x_1 + int((i * 1.732 + parity_ind * 0.866 + 0.866) * side_size),
                   bias_y_1 + int((j * 1.5 + 0) * side_size))])

        if self.agent_pos:
            painter.setBrush(candy_colors_gui[self.candy_type].lighter(200))
        else:
            painter.setBrush(candy_colors_gui[self.candy_type])

        painter.drawPolygon(points)


class Client_net:
    """
    Klasa sluzaca do polaczenia przez serwer z innym graczem
    """

    def __init__(self, host, port, buff_size):
        self.host = host
        self.port = port
        self.buff_size = buff_size

        self.addr = (self.host, self.port)

        # self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(self.addr)
        except Exception as e:
            print(f"Connection error: {str(e)}")

    def disconnect(self):
        self.client_socket.send(bytes("q", "utf-8"))
        self.client_socket.close()

    def send(self, message):
        try:
            self.client_socket.send(bytes(message, "utf-8"))
        except Exception as e:
            print(f"Sending error: {str(e)}")

    def reciv(self):
        return self.client_socket.recv(self.buff_size).decode("utf-8")


class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.env = Environment(15, 20)

        self.player_1 = Agent(1)
        self.player_2 = Agent(2)

        self.current_player = 0
        self.moving_locked = False
        self.hot_seat = True

        # Polaczenie przez siec

        # QGraphics
        # ----------------------------------------------
        offset_1_x, offset_1_y, view_size_x, view_size_y = 20, 20, 400, 250

        self.view1 = QGraphicsView(self.env.scene_1, self)
        self.view1.setGeometry(offset_1_x, offset_1_y, view_size_x, view_size_y)

        offset_2_x, offset_2_y = offset_1_x + view_size_x + 100, offset_1_y
        self.view2 = QGraphicsView(self.env.scene_2, self)
        self.view2.setGeometry(offset_2_x, offset_2_y, view_size_x, view_size_y)
        # ----------------------------------------------

        # Siec
        # ----------------------------------------------
        self.board_separator = ";"
        self.play_online = False
        self.made_move = False

        self.addr = HOST
        self.port = PORT

        self.cl_net = Client_net(self.addr, self.port, 1024)

        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.handle_messages)

        # ----------------------------------------------

        # Pliki
        # ----------------------------------------------
        self.new_root = ET.Element("root")

        # ----------------------------------------------


        # Przyciski
        self.ui.exitButton.clicked.connect(self.exit_game)
        self.ui.newGameButton.clicked.connect(self.new_game)
        self.ui.onlineButton.clicked.connect(self.set_online)
        # Poruszanie
        self.ui.rightButton.clicked.connect(self.right)
        self.ui.upRightButton.clicked.connect(self.up_right)
        self.ui.upLeftButton.clicked.connect(self.up_left)
        self.ui.leftButton.clicked.connect(self.left)
        self.ui.bottomLeftButton.clicked.connect(self.bottom_left)
        self.ui.bottomRightButton.clicked.connect(self.bottom_right)
        self.ui.chooseCandyButton.clicked.connect(self.lock_movement)
        # Pliki
        self.ui.saveHistButton.clicked.connect(self.save_history_to_xml)
        self.ui.saveConfButton.clicked.connect(self.save_conf_json)
        self.ui.chooseConfButton.clicked.connect(self.choose_conf)
        self.ui.loadConfButton.clicked.connect(self.load_conf_json)
        self.ui.loadSavetButton.clicked.connect(self.load_save_xml)

    def paintEvent(self, event):
        """
        Uaktualnienie informacji poza widokami - punkty i obecny gracz
        """

        if self.play_online:
            player_text = "You" if self.current_player == 0 else "Opponent"
        else:
            player_text = self.current_player + 1
        self.ui.currentPlayerlabel.setText(f"Current player: {player_text}")
        self.ui.player1PointsLabel.setText(f"Player 1: {self.player_1.points}")
        self.ui.player2PointsLabel.setText(f"Player 2: {self.player_2.points}")

        # Uaktulanienie wyswietlania
        self.update()

    def new_game(self):
        """
        Rozpoczie nowej gry
        :return: None
        """
        self.env = Environment(15, 20)

        self.player_1 = Agent(1)
        self.player_2 = Agent(2)

        self.current_player = 0
        self.moving_locked = False

        self.view1.setScene(self.env.scene_1)
        self.view2.setScene(self.env.scene_2)

        self.new_root = ET.Element("root")  # XML

    def exit_game(self):
        sys.exit(2)

    def lock_movement(self):
        self.moving_locked = not self.moving_locked

    def choose_move(self, direction_no):
        """
        Wykonanie ruchu, uaktualnienie planszy i punktow
        :param direction_no: numer kierunku do wykonania ruchu
        :return: None
        """
        # Ustalenie, ktory gracz wykonuje ruch
        if self.current_player == 0:
            agent = self.player_1
            board = self.env.board_1
        elif self.current_player == 1:
            agent = self.player_2
            board = self.env.board_2
        else:
            return  # Gdy zaden z graczy ma nie wykonywac ruchu

        # Nowa pozycja
        new_pos_y, new_pos_x = self.env.next_pos_in_direction(agent.pos_y, agent.pos_x, direction_no)
        if new_pos_x < 0 or new_pos_x > self.env.size_x - 1 or new_pos_y < 0 or new_pos_y > self.env.size_y - 1:
            return

        if not self.moving_locked:
            # przesuniecie pozycji agenta
            agent.pos_y, agent.pos_x = new_pos_y, new_pos_x
        else:
            # zamiana cukierkow
            if self.current_player == 0:
                self.add_board_to_xml(self.new_root)  # zapisanie ruchu do XML

            agent.make_move(self.env, board, direction_no)
            self.moving_locked = False
            self.current_player = (self.current_player + 1) % 2
            points = self.env.update_board(board)
            agent.points += points
            self.made_move = True  # Do wysylania przez siec


        if self.env.curr_player == 0:
            # Uaktualnienie wygladu cukierkow (wraz z zaznaczeniem obecnej pozycji agenta)
            for c in self.env.scene_1.items():
                c.agent_pos = False
                if c.y == agent.pos_y and c.x == agent.pos_x:
                    c.agent_pos = True
                c.update()
        elif self.env.curr_player == 1:
            for c in self.env.scene_2.items():
                c.agent_pos = False
                if c.y == agent.pos_y and c.x == agent.pos_x:
                    c.agent_pos = True
                c.update()

        self.env.curr_player = self.current_player

    def right(self):
        direction_no = 0
        self.choose_move(direction_no)

    def up_right(self):
        direction_no = 1
        self.choose_move(direction_no)

    def up_left(self):
        direction_no = 2
        self.choose_move(direction_no)

    def left(self):
        direction_no = 3
        self.choose_move(direction_no)

    def bottom_left(self):
        direction_no = 4
        self.choose_move(direction_no)

    def bottom_right(self):
        direction_no = 5
        self.choose_move(direction_no)

    def set_online(self):
        """
        Metoda wywolywana przy wybraniu trybu online
        :return: None
        """
        if not self.play_online:
            # Rozpoczecie gry online
            self.cl_net = Client_net(self.addr, self.port, 1024)

            self.cl_net.connect()
            self.cl_net.send("init")
            self.play_online = True
            self.new_game()
            self.made_move = False

            self.timer.start()
        else:
            self.timer.stop()
            self.play_online = False

            self.cl_net.disconnect()
            self.new_game()

    def handle_messages(self):
        """
        Metoda do obslugi wiadmosci przychodzacych i wysylania wiadomosci na serwer
        :return: None
        """

        # Odebranie wiadomosci w postaci stringa i ewentualne zaktualizoawanie obecnego stanu
        msg_rec = self.cl_net.reciv()
        if msg_rec == "req":  # Zadanie wyslania
            pass  # Samo wyslanie
        elif msg_rec == "q":
            # Dostana wiadomosc o wyjsciu - efekt jak wcisniecie przycisku online. Skutkuje to tez wyslaniem
            # wiadomosci na serwer
            self.set_online()
            return
        elif not self.made_move:
            # Zmiana lokalnego stanu
            self.change_both_from_string(msg_rec)

        # Utworzenie wiadomosci do wyslania
        msg_send = self.get_string_board_state()

        made_move_send = "3" if self.made_move else "0"
        points_send = str(self.player_1.points)

        msg_send = made_move_send + self.board_separator + points_send + self.board_separator + msg_send
        self.cl_net.send(msg_send)

        self.made_move = False

    def change_both_from_string(self, message):
        """
        Przeksztalcenie wiadomosci w postaci stringa, i uaktualnienie planszy
        :param message: string zawierajacy wiadomosc dotyczaca nowych planszy
        :return: None
        """

        is_active, opponent_points, m_1, m_2 = message.split(self.board_separator)

        if is_active == "0":
            self.current_player = 0
            self.env.curr_player = 0
        else:
            self.current_player = -1
            self.env.curr_player = -1

        self.player_2.points = int(opponent_points)

        new_b_1, new_b_2 = [], []
        for i in range(len(m_1)):
            new_b_1.append(int(m_1[i]))
            new_b_2.append(int(m_2[i]))

        self.env.change_board(new_b_1, 0)
        self.env.change_board(new_b_2, 1)

        for c in self.env.scene_1.items():
            c.update()
        for c in self.env.scene_2.items():
            c.update()

    def get_string_board_state(self, separate=False):
        """
        Stworzenie wiadomosci na podstawie lokalnego stanu gry
        :return: wiadomosc do wyslania (string)
        """

        b_1, b_2 = [], []  # Listy intow
        self.env.get_int_board(b_1, 0)
        self.env.get_int_board(b_2, 1)

        # Dolaczenie do wiadomosci informacji o stanie planszy w postaci znakow
        candy_separator = ''
        b_1 = f'{candy_separator}'.join(str(i) for i in b_1)
        b_2 = f'{candy_separator}'.join(str(i) for i in b_2)

        if separate:
            return b_1, b_2

        message = b_1 + self.board_separator + b_2

        return message

    def save_history_to_xml(self):
        """
        Zapisanie historii rozgrywki do pliku history.xml
        :return: None
        """
        new_tree = ET.ElementTree(self.new_root)
        new_tree.write("history.xml")

    def add_board_to_xml(self, root):
        """
        Zapisanie obecnych danych z rozgrywki (plansze, punkty) do pliku xml
        :param root: korzen xml
        :return: None
        """
        #
        step = ET.SubElement(root, "step")  # Element odpowiadajacy jednemu krokowi w rozgrywce

        # Element planszy 1: jako zawartosc -  plansza z typami cukierkow, jako atrybuty - numery graczy, ich punkty
        # i pozycja
        board1 = ET.SubElement(step, 'board')
        board1.attrib["player"] = "1"
        board1.attrib["points"] = str(self.player_1.points)
        board1.attrib["player_position"] = str(self.player_1.pos_y) + "," + str(self.player_1.pos_x)

        # Plansza 2
        board2 = ET.SubElement(step, 'board')
        board2.attrib["player"] = "2"
        board2.attrib["points"] = str(self.player_2.points)
        board2.attrib["player_position"] = str(self.player_2.pos_y) + "," + str(self.player_2.pos_x)

        # Zawartosc planszy
        board1.text, board2.text = self.get_string_board_state(separate=True)

    def save_conf_json(self):
        """
        Zapisanie obecnej konfiguracji (port i adres do polaczenia) do pliku json (data.json)
        :return: None
        """

        conf_data = {}
        conf_data["port"] = str(self.port)
        conf_data["addr"] = self.addr

        with open('configuration.json', 'w', encoding='utf-8') as f:
            json.dump(conf_data, f, ensure_ascii=False, indent=4)

    def choose_conf(self):
        """
        Zaladowuje port i adres z texboxow, do zmiennycyh w programie
        :return: None
        """
        try:
            self.port = int(self.ui.portLineEdit.text())
            self.addr = self.ui.addrLineEdit.text()
        except Exception as e:
            s = str(e)
            print(f"choose conf error: {s}")

    def load_conf_json(self):
        """
        Wczytanie danych konfiguracyjnych (port i adres do polaczenia) z pliku json
        :return: None
        """
        try:
            with open('configuration.json', encoding='utf-8') as f:
                conf_data = json.load(f)
                self.port = int(conf_data["port"])
                self.addr = conf_data["addr"]
            self.ui.portLineEdit.setText(str(self.port))
            self.ui.addrLineEdit.setText(self.addr)
        except Exception as e:
            s = str(e)
            print(f"load conf error: {s}")

    def load_save_xml(self):
        """
        Wczytanie stanu gry z xml-a
        :return: None
        """
        try:
            tree = ET.parse('history.xml')
            root = tree.getroot()

            last_step = root[-1]  # Do wczytania save'a - pobranie ostatniego kroku

            board_1, board_2 = last_step[0], last_step[1]  # Odpowiednei tablice

            # Wczytanie punktow
            self.player_1.points = int(board_1.attrib["points"])
            self.player_2.points = int(board_2.attrib["points"])

            # Zamiana typow cukierkow z tablic w postaci zmienncy string
            new_b_1, new_b_2 = [], []

            for i in range(self.env.size_y*self.env.size_x):
                try:
                    new_b_1.append(int(board_1.text[i]))
                    new_b_2.append(int(board_2.text[i]))
                except:
                    pass
            self.env.change_board(new_b_1, 0)
            self.env.change_board(new_b_2, 1)

            for c in self.env.scene_1.items():
                c.update()
            for c in self.env.scene_2.items():
                c.update()
        except Exception as e:
            s = str(e)
            print(f"load save error: {s}")


class Environment:
    def __init__(self, size_y, size_x):

        self.number_of_types = 7
        self.candy_colors = candy_colors
        self.candy_shapes = [u"\u25A1", u"\u25A3", u"\u25C6", u"\u25D1", u"\u25E9", u"\u25D8", u"\u25A1", " "]
        self.direction_list = [[0, 1], [-1, 1], [-1, -1], [0, -1], [1, -1], [1, 1]]
        self.new_candy_type = 0
        self.curr_player = 0

        self.board_1 = []
        self.board_2 = []
        
        self.size_y, self.size_x = size_y, size_x

        # Stworzenie plansz
        self.boards_created = False  # Zmienna potrzebna do zdecydowania czy dodawac  cukierki do sceny, podczas aktualizacji
        self.create_board(self.board_1)
        self.update_board(self.board_1)

        self.create_board(self.board_2)
        for j in range(len(self.board_2)):  # Utworzenie kopii planszy - ta sama plansza startowa
            for i in range(len(self.board_2[j])):
                copy_candy(self.board_2[j][i], self.board_1[j][i])
        self.boards_created = True

        # --------------------------------------------
        self.scene_1 = QGraphicsScene()
        self.scene_2 = QGraphicsScene()
        self.paint_scene()  # poczatkowe narysowanie sceny
        # --------------------------------------------

    def change_board(self, new_board, player_no):
        """
        Uaktualnienie tablicy na podstawie przeslanej
        :param new_board: nowa plansza - lista plaska (1D) liczb (typow cukierkow)
        :param player_no: okreslenie numeru gracza, ktorego plansza ma byc kopiowana
        :return: None
        """

        if player_no == 0:
            board = self.board_1
        else:
            board = self.board_2

        new_board_counter = 0
        for j in range(self.size_y):
            for i in range(self.size_x):
                board[j][i].candy_type = new_board[new_board_counter]
                new_board_counter += 1

    def get_int_board(self, int_board, player_no):
        """
        Tworzy mape typow cukierkow (int) zamiast listy obiektow
        :param int_board: pusta lista, zotana do niej dopisane typy cukierkow (w plaskiej formie 1d)
        :param player_no: numer planszy do zapisania
        :return: None
        """
        if player_no == 0:
            board = self.board_1
        else:
            board = self.board_2

        for j in range(self.size_y):
            for i in range(self.size_x):
                int_board.append(board[j][i].candy_type)

    def paint_scene(self):
        """
        Narysowanie sceny na poczatku rozgrywki - dodanie elementow z tablic do scen
        :return: None
        """
        self.scene_1.clear()
        self.scene_2.clear()

        self.board_1[0][0].agent_pos = True # Poczatkowa pozycja agentow
        self.board_2[0][0].agent_pos = True

        for j, y in enumerate(self.board_1):
            for i, candy in enumerate(y):
                try:
                    self.scene_1.addItem(candy)
                except Exception as e:
                    s = str(e)
                    print(s)
        for j, y in enumerate(self.board_2):
            for i, candy in enumerate(y):
                try:
                    self.scene_2.addItem(candy)
                except Exception as e:
                    s = str(e)
                    print(s)

    def create_board(self, board):
        """
        Stowrzenie planszy cukierkow o okreslonym rozmiarze
        :return:
        """
        for j in range(self.size_y):
            board.append([])
            for i in range(self.size_x):
                board[j].append(Candy(candy_type=-1, y=j, x=i))

    def next_pos_in_direction(self, pos_y, pos_x, direction):
        """
        Ustalenie indeksu pola sasiedniego, w danym kierunku
        :param pos_y: pozycja pola wejsciowego - y
        :param pos_x: pozycja pola wejsciowego - x
        :param direction: kierunek poruszania (lewo, prawo, gora-prawo, gora-lewo, dol-prawo, dol-lewo)
        lub direction_no - wtedy int - numer kierunku z direction_list

        :return: new_pos_y, new_pos_x - pozycje pola sasiedniego
        """
        if type(direction) == int:
            direction = self.direction_list[direction]

        new_pos_y = pos_y
        new_pos_x = pos_x
        if direction[0] == 0:
            # zmiany poziome - normalnie
            new_pos_y += direction[0]
            new_pos_x += direction[1]
        else:
            if new_pos_y % 2 == 0 and direction[1] == -1:
                # na ukos, w lewo - rząd parzysty
                new_pos_x += direction[1]
            elif new_pos_y % 2 == 1 and direction[1] == 1:
                # na ukos, w prawo - rząd nieparzysty
                new_pos_x += direction[1]
            new_pos_y += direction[0]
            # w pozostalych przypadkach - w prawo, rzad parzysty i w lewo rzad nieparzysty zmienia sie
            # jedynie indeks wiersza

        return new_pos_y, new_pos_x

    def check_in_row(self, board, pos_y, pos_x, direction, candy_type):
        """
        Sprawdzenie, czy sa co najmniej 3 cukierki tego samego typu w danym kierunku
        :param pos_y: pozycja klocka startowego - y
        :param pos_x: pozycja klocka startowego - x
        :param direction: kierunek sprawdzania
        :param candy_type: typ cukierka
        :return: lista pozycji tego samego typu, jesli sa min 3 z rzedu, jesli nie - pusta lista
        """
        same_type = True
        i = 1
        candies_to_erase = [(pos_y, pos_x)]
        new_pos_y = pos_y
        new_pos_x = pos_x
        while same_type:
            new_pos_y, new_pos_x = self.next_pos_in_direction(new_pos_y, new_pos_x, direction)

            # Wyjscie poza tablice
            if new_pos_y < 0 or new_pos_y > self.size_y-1:
                same_type = False
            elif new_pos_x < 0 or new_pos_x > self.size_x - 1:
                same_type = False

            if same_type:
                if board[new_pos_y][new_pos_x].candy_type == candy_type:
                    candies_to_erase.append((new_pos_y, new_pos_x))
                    i += 1
                else:
                    same_type = False

        if i >= 3:
            return candies_to_erase
        else:
            return []

    def check_matches(self, board):
        """
        Sprawdzenie wszystkich dostepnych ciagow do usuniecia
        :return: None
        """
        candies_to_erase = []  # lista pozycji do usuniecia

        for j, y in enumerate(board):
            for i, x in enumerate(y):

                candies_to_erase.append(self.check_in_row(board, j, i, (0, 1), board[j][i].candy_type))  # right
                candies_to_erase.append(self.check_in_row(board, j, i, (-1, 1), board[j][i].candy_type))  # up, right
                candies_to_erase.append(self.check_in_row(board, j, i, (-1, -1), board[j][i].candy_type))  # up, left

        for c_list in candies_to_erase:
            for c_pos in c_list:
                board[c_pos[0]][c_pos[1]].candy_type = self.number_of_types

    def swap(self, board, pos_1, pos_2):
        board[pos_1[0]][pos_1[1]], board[pos_2[0]][pos_2[1]] = board[pos_2[0]][pos_2[1]], board[pos_1[0]][pos_1[1]]

    def check_full(self, board):
        """
        Sprawdzenie czy tablica cukierkow jest pelna (brak pustych pol)
        :return: True - pelna tablica, False -tablica zawiera min 1 puste pole
        """
        for y in board:
            for candy in y:
                if candy.candy_type == self.number_of_types:
                    return False
        return True

    def count_empty(self,  board):
        """
        Zlicz liczbe pustych pol
        :return: liczba pustych pol
        """
        empty_count = 0
        for y in board:
            for candy in y:
                if candy.candy_type == self.number_of_types:
                    empty_count += 1
        return empty_count

    def move_down(self,  board):
        """
        Przesuniecie cukierkow na dol, tak by nie bylo pustych pol
        :return: None
        """

        full_board = False
        while not full_board:
            for j, y in reversed(list(enumerate(board))):
                for i, candy in enumerate(y):
                    if candy.candy_type == self.number_of_types:  # Puste pole
                        # Wylosowanie kierunku - czy opada z gory z prawej, czy z lewej
                        direction = [-1, -1 if random.randrange(0, 2) == 0 else 1]
                        next_pos_y, next_pos_x = self.next_pos_in_direction(j, i, direction)
                        if next_pos_y < 0 or next_pos_x < 0 or next_pos_x > len(y)-1:
                            # U gory lub z boku - wyjscie poza plansze - losowanie nowego cukierka
                            board[j][i].candy_type = self.new_candy_type
                            self.new_candy_type = (self.new_candy_type + 1) % self.number_of_types
                        elif board[next_pos_y][next_pos_x].candy_type != self.number_of_types:
                            # Normalny spadek
                            self.swap(board, (next_pos_y, next_pos_x), (j, i))
                        else:
                            # Na gorze tez jest pusto
                            direction[1] = -direction[1]  # Zamiana kierunku (lewo, prawo)

                            # powtorzony schemat - jesli bedzie z drugiej strony tez pusto,
                            # to trezeba bedzie liste przejsc jeszcze raz
                            next_pos_y, next_pos_x = self.next_pos_in_direction(j, i, direction)
                            if next_pos_y < 0 or next_pos_x < 0 or next_pos_x > len(y) - 1:
                                # U gory lub z boku - wyjscie poza plansze - losowanie nowego cukierka
                                board[j][i].candy_type = self.new_candy_type

                            else:
                                self.swap(board, (next_pos_y, next_pos_x), (j, i))
            full_board = self.check_full(board)

    def update_board(self, board):
        """
        Uaktualnienie planszy - wyszukanie i usuniecie wszystkich 3, przesuniecie na dol (w oddzielnej petli) Jesli w
        pierwszym kroku nie zostaly znalezioen zadne 3, to proces jest zakanczany, jesli zostaly to jest powtarzany
        od nowa -  nowe 3, ktore mogly powstac po spadku
        :return: points_sum - liczba punktow - pustych pol, ktore pojawily sie pojawily
        """

        points_sum = 0
        movement_finished = False
        while not movement_finished:
            # sprzwdzanie cz
            self.check_matches(board)
            points = self.count_empty(board)  # liczba pustych pol (ktore sie pojawily) - punkty
            points_sum += points
            full_board = False
            if points > 0:
                # Pojawienie sie nowych pustych pol - przesuniecie w dol
                while not full_board:
                    # Przesuniecie na dol - takze gdy sa puste pola nie zapelnione po jednym przesunieciu -
                    # gdy puste pole ma 2 puste wartosci nad soba
                    self.move_down(board)
                    if self.check_full(board):
                        full_board = True
            else:
                movement_finished = True

        for j in range(len(board)):  # Uaktualnienie argumentow y i x w elementach typu Candy - polach
            for i in range(len(board[j])):
                board[j][i].y = j
                board[j][i].x = i

        return points_sum


class Agent:
    def __init__(self, player_number):
        self.player_number = player_number
        self.points = 0
        self.pos_y, self.pos_x = 0, 0  # Pozycja agenta w tablicy - wybrany cukierek
        self.direction = [0, 1]  # Wybrany kierunek zamiany (dostepne: [0,1], [0,-1], [1,1], [1,-1], [-1,1], [-1,-1])

    def swap_agent(self, board, pos_1, pos_2):
        """
        Zamiana pozycji cukierkow
        :param board: plansza
        :param pos_1: pozycja pierwsza
        :param pos_2: pozycja druga
        :return: None
        """
        board[pos_1[0]][pos_1[1]], board[pos_2[0]][pos_2[1]] = board[pos_2[0]][pos_2[1]], board[pos_1[0]][pos_1[1]]

    def make_move(self, env, board, direction_no):
        """
        Zrobienie ruchu (i pobranie informacji o nim z konsoli)
        :param env - srodowisko
        :return: None
        """
        pos_y = self.pos_y
        pos_x = self.pos_x
        direction_no = int(direction_no)

        if pos_y >= 0 and pos_y < env.size_y and pos_x >= 0 and pos_x < env.size_x \
                and direction_no >= 0 and direction_no <= 5:
            direction = env.direction_list[direction_no]
            new_pos_y, new_pos_x = env.next_pos_in_direction(pos_y, pos_x, direction)
            if new_pos_y >= 0 and new_pos_y < env.size_y and new_pos_x >= 0 and new_pos_x < env.size_x:
                pass
            else:
                return
        else:
            return

        self.direction = direction
        self.pos_y, self.pos_x = pos_y, pos_x
        self.swap_agent(board, (self.pos_y, self.pos_x), (new_pos_y, new_pos_x))


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    my_app = MyApp()
    my_app.show()



    sys.exit(app.exec_())


















