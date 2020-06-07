import socket
from threading import Thread

PORT = 5555
HOST = "localhost"


class Server(object):

    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.port = 5555
        self.buff_size = 1024
        self.host = HOST

        # Zmienne odpowaiadajace czy dani gracze sa podlaczeni
        self.player_1 = False
        self.player_2 = False

        # Obecny gracz, ktory ma ruch
        self.active_player = 0

        # Punkty graczy
        self.points_1 = 0
        self.points_2 = 0

        # Plansze graczy
        self.board_1 = None
        self.board_2 = None

        # Zmienna ustawiana gdy jeden z graczy opusci gre - gra jest wtedy zamykana
        self.quit_game = False

        # Odpalenie serwera
        try:
            self.server_socket.bind((self.host, self.port))
        except socket.error as e:
            print(str(e))

        self.server_socket.listen(2)
        print("Waiting for a connection")

        self.run()

    def run(self):
        while True:
            if not (self.player_1 and self.player_2):
                client_con, addr = self.server_socket.accept()
                Thread(target=self.handle_client, args=(client_con, addr)).start()

    def handle_client(self, client_con, addr):
        self.quit_game = False  # Przy podlaczeniu sie ustawienie zmiennej wymuszajacej wyjscie na False
        if not self.player_1:
            self.player_1 = True
            id_p = 0
        elif not self.player_2:
            self.player_2 = True
            id_p = 1

        while True:
            # Odebranie wiadomosci i zdekodowanie jej do stringa
            message_rec = client_con.recv(self.buff_size).decode("utf-8")

            if message_rec == "init":
                # Wiadomosc inicjalizujaca
                if id_p == 0:  # Dla pierwszego gracza nie rob nic
                    client_con.sendto(bytes("req", "utf-8"), addr)  # State request
                else:  # Dla nastepnego wyslij poczatkowy stan gry
                    msg_to_send = "2" + ";" + "0" + ";" + self.board_2 + ";" + self.board_1
                    client_con.sendto(bytes(msg_to_send, "utf-8"), addr)
            elif message_rec != "q":
                # Wiadomosc z informacja czy zostal wykonany ruch, punktami oraz planszami

                # Podzial wiadomosci
                move_made, points, board_1, board_2 = message_rec.split(";")

                move_made = False if move_made == "0" else True

                if id_p == 0:
                    if self.active_player == 0 and move_made:
                        # Wykonano ruch - zmiana aktywnego gracza
                        self.active_player = 1
                elif id_p == 1:
                    if self.active_player == 1 and move_made:
                        # Wykonanao ruch - zmiana aktywnego gracza
                        self.active_player = 0

                # Wiadomosc do wyslania
                is_active = "0" if id_p == self.active_player else "2"  # aktywny-0, nieaktywy - co innego
                if id_p == 0:
                    self.board_1 = board_1  # Uaktualnienie planszy
                    self.points_1 = int(points)  # Uaktualnienie punktow

                    points_to_send = str(self.points_2)
                    if self.board_2 is None:
                        self.board_2 = board_2
                    my_board, opponent_board = self.board_1, self.board_2
                elif id_p == 1:
                    self.board_2 = board_1  # Uaktualnienie planszy
                    self.points_2 = int(points)  # Uaktualnienie punktow

                    points_to_send = str(self.points_1)
                    my_board, opponent_board = self.board_2, self.board_1

                msg_to_send = is_active + ";" + points_to_send + ";" + my_board + ";" + opponent_board

                if self.quit_game:
                    # Inny gracz wyszedl z gry - wyslanie wiadomosci o wyjsciu do drugiego gracza
                    client_con.sendto(bytes("q", "utf-8"), addr)
                else:
                    # Normalna wiadomosc
                    client_con.sendto(bytes(msg_to_send, "utf-8"), addr)
            else:
                # Wylaczenie klienta
                self.quit_game = True
                client_con.close()
                break

        if id_p == 0:
            self.player_1 = False
        elif id_p == 1:
            self.player_2 = False

        # Wyczyszczenie tablic po wyjsciu graczy
        if not self.player_1 and not self.player_2:
            self.board_1 = None
            self.board_2 = None


s = Server()










