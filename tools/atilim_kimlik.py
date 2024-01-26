import configparser
import json
import pickle
import requests
from datetime import datetime, timedelta
from pathlib import Path
from tools.exceptions import LoginError, IPBanned


class AtilimAuth:
    domain: str = "atilim.edu.tr"
    referer: str = f"https://kimlik.{domain}"
    login_url: str = f"{referer}/ui/login"
    user_agent: str = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.207.132.170 "
                       "Safari/537.36")
    path = Path(__file__).parent.parent
    session_file: Path = Path(f"{path}/atilim_data/atilim-session")

    def __init__(self):
        self.config: configparser.ConfigParser = configparser.ConfigParser()
        self.config_file: str = f"{self.path}/atilim_data/auth_atilim.ini"

        try:
            if Path(self.config_file).exists():
                self.config.read(self.config_file)
                self.username: str = self.config["auth"]["username"]
                self.password: str = self.config["auth"]["password"]
            else:
                self.username, self.password = self.create_config_file()
        except Exception as e:
            print(f"Error reading configuration file: {e}")

    def create_config_file(self) -> tuple:
        username: str = str(input("Enter your Atilim University username: "))
        password: str = str(input("Enter your Atilim University password: "))
        with open(self.config_file, "w") as configfile:
            self.config["auth"] = {
                "username": username,
                "password": password
            }
            self.config.write(configfile)
        return username, password

    def get_session(self) -> requests.Session:
        with requests.Session() as session:
            session.headers.update({
                "Connection": "keep-alive",
                "Referer": self.referer,
                "User-Agent": self.user_agent
            })
            payload = {"loginName": self.username, "passwd": self.password}
            post = session.post(self.login_url, json=payload)
            if post.status_code == 504:
                raise IPBanned("Your IP Address is Banned")
            if json.loads(post.content)["success"] is False:
                raise LoginError("Invalid username or password")
            else:
                with self.session_file.open("wb") as s:
                    pickle.dump(session, s)
                    print("Session Stored - You Logged Into System")
            return session

    def login(self) -> requests.Session:
        if self.session_file.exists():
            m_time = self.session_file.stat().st_mtime
            mtime = datetime.fromtimestamp(m_time)
            now = datetime.now()
            elapsed = now - mtime
            if elapsed > timedelta(minutes=20):
                return self.get_session()
            else:
                with requests.Session() as session:
                    with self.session_file.open("rb") as s:
                        saved_session = pickle.load(s)
                        session.cookies.update(saved_session.cookies)
                        print("Stored Session Used - No Required Login")
                        session.headers.update({"User-Agent": self.user_agent})
                    return session
        else:
            return self.get_session()
