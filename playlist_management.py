import os

# VLC installation path
os.add_dll_directory(r"C:\Program Files\VideoLAN\VLC")

import vlc


class Node:
    def __init__(self, title, artist, filepath):
        self.title = title
        self.artist = artist
        self.filepath = filepath
        self.next = None


class CircularPlaylist:
    def __init__(self):
        self.tail = None
        self.current = None
        self.player = None
        self.mode = "Audio"

    # Stop current audio or video
    def stop_audio(self):
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass

            self.player = None

    # Identify media type using file extension
    def get_media_type(self, node):
        extension = os.path.splitext(node.filepath)[1].lower()

        audio_formats = [
            ".mp3", ".wav", ".aac", ".flac",
            ".ogg", ".m4a", ".wma"
        ]

        video_formats = [
            ".mp4", ".mkv", ".avi", ".mov",
            ".wmv", ".flv", ".webm", ".mpeg",
            ".mpg", ".3gp", ".m4v"
        ]

        if extension in audio_formats:
            return "Audio"

        elif extension in video_formats:
            return "Video"

        return "Unknown"

    # Add song or video
    def add(self, title, artist, filepath):
        title = title.strip()
        artist = artist.strip()
        filepath = filepath.strip().strip('"').strip("'")

        if not title or not artist or not filepath:
            return "All fields are required."

        if not os.path.isfile(filepath):
            return "Media file not found. Check the file path."

        media_type = self.get_media_type(
            Node(title, artist, filepath)
        )

        if media_type == "Unknown":
            return "Unsupported media format."

        if self.search(title):
            return "Track already exists!"

        node = Node(title, artist, os.path.abspath(filepath))

        if self.tail is None:
            self.tail = node
            node.next = node
        else:
            node.next = self.tail.next
            self.tail.next = node
            self.tail = node

        # Select media if it matches the current mode
        if self.current is None and media_type == self.mode:
            self.current = node

        return "Media added successfully!"

    # Display all media
    def display(self):
        items = []

        if self.tail is None:
            return items

        temp = self.tail.next

        while True:
            items.append(temp)
            temp = temp.next

            if temp == self.tail.next:
                break

        return items

    # Search media by title
    def search(self, title):
        if self.tail is None:
            return None

        title = title.strip().lower()
        temp = self.tail.next

        while True:
            if temp.title.lower() == title:
                return temp

            temp = temp.next

            if temp == self.tail.next:
                break

        return None

    # Get media matching selected mode
    def get_mode_items(self):
        items = self.display()

        return [
            item for item in items
            if self.get_media_type(item) == self.mode
        ]

    # Select Audio or Video mode
    def set_mode(self, mode):
        self.stop_audio()
        self.mode = mode
        self.current = None

        items = self.get_mode_items()

        if items:
            self.current = items[0]

        print("\nMode changed to:", self.mode)

        if self.current:
            print("Selected:", self.current.title)
        else:
            print("No", self.mode, "files available.")

    # Play current song or video
    def play_current(self):
        if self.current is None:
            print("No", self.mode, "files available.")
            return

        if self.get_media_type(self.current) != self.mode:
            print("Please select media matching the current mode.")
            return

        try:
            self.stop_audio()

            filepath = os.path.abspath(self.current.filepath)

            self.player = vlc.MediaPlayer(filepath)

            result = self.player.play()

            if result == -1:
                print("VLC could not start playback.")
                self.player = None
                return

            print("\nNow Playing:", self.current.title)
            print("Artist:", self.current.artist)
            print("Media Type:", self.mode)
            print("File:", filepath)

            if self.mode == "Video":
                print("Video is opening through VLC.")

        except Exception as error:
            print("Playback error:", error)
            self.player = None

    # Play next media of selected mode
    def next_track(self):
        items = self.get_mode_items()

        if not items:
            print("No", self.mode, "files available.")
            return

        if self.current not in items:
            self.current = items[0]
        else:
            index = items.index(self.current)
            self.current = items[(index + 1) % len(items)]

        self.play_current()

    # Play previous media of selected mode
    def previous_track(self):
        items = self.get_mode_items()

        if not items:
            print("No", self.mode, "files available.")
            return

        if self.current not in items:
            self.current = items[0]
        else:
            index = items.index(self.current)
            self.current = items[(index - 1) % len(items)]

        self.play_current()

    # Show current media
    def current_track(self):
        return self.current

    # Delete media by title
    def delete(self, title):
        if self.tail is None:
            return "Playlist is empty."

        title = title.strip().lower()

        previous = self.tail
        node = self.tail.next

        while True:
            if node.title.lower() == title:

                # Only one node in playlist
                if node == self.tail and node.next == node:
                    self.stop_audio()
                    self.tail = None
                    self.current = None

                else:
                    # If deleting current media
                    if self.current == node:
                        self.stop_audio()
                        self.current = None

                    previous.next = node.next

                    if node == self.tail:
                        self.tail = previous

                # Select another media in current mode if needed
                if self.current is None:
                    items = self.get_mode_items()

                    if items:
                        self.current = items[0]

                return "Media deleted successfully!"

            previous = node
            node = node.next

            if node == self.tail.next:
                break

        return "Media not found."

    # Sort playlist by title
    def sort_by_title(self):
        if self.tail is None:
            return "Playlist is empty."

        items = self.display()
        items.sort(key=lambda node: node.title.lower())

        # Stop playback before sorting
        self.stop_audio()

        self.tail = None
        self.current = None

        # Rebuild circular linked list
        for item in items:
            node = Node(item.title, item.artist, item.filepath)

            if self.tail is None:
                self.tail = node
                node.next = node
            else:
                node.next = self.tail.next
                self.tail.next = node
                self.tail = node

        # Select first media matching current mode
        mode_items = self.get_mode_items()

        if mode_items:
            self.current = mode_items[0]

        return "Playlist sorted successfully!"


def main():
    print("Program is starting...")

    # Initialize VLC
    try:
        vlc_instance = vlc.Instance()

        if vlc_instance is None:
            print("VLC could not initialize. Install VLC Media Player.")
            return

    except Exception as error:
        print("VLC initialization error:", error)
        print("Install VLC Media Player and python-vlc, then try again.")
        return

    playlist = CircularPlaylist()

    # Ask user's preferred media mode
    print("\n===== SELECT MEDIA MODE =====")
    print("1. Audio Mode")
    print("2. Video Mode")

    mode_choice = input("Choose mode: ").strip()

    if mode_choice == "1":
        playlist.set_mode("Audio")

    elif mode_choice == "2":
        playlist.set_mode("Video")

    else:
        print("Invalid choice. Defaulting to Audio Mode.")
        playlist.set_mode("Audio")

    while True:
        print("\n===== MUSIC / MEDIA PLAYLIST MANAGER =====")
        print("Current Mode:", playlist.mode)
        print("1. Add Song/Media")
        print("2. Delete Song/Media")
        print("3. Display Playlist")
        print("4. Search Song/Media")
        print("5. Play Current Song/Media")
        print("6. Next Song/Media")
        print("7. Previous Song/Media")
        print("8. Show Current Song/Media")
        print("9. Sort Playlist")
        print("10. Stop Playback")
        print("11. Change Audio/Video Mode")
        print("0. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            title = input("Enter song/media title: ")
            artist = input("Enter artist name: ")
            filepath = input("Enter full media file path: ")

            print(playlist.add(title, artist, filepath))

        elif choice == "2":
            title = input("Enter title to delete: ")
            print(playlist.delete(title))

        elif choice == "3":
            print("\n===== DISPLAY PLAYLIST =====")

            items = playlist.display()

            if not items:
                print("Playlist is empty.")

            else:
                for i, item in enumerate(items, 1):
                    marker = (
                        " <-- Current"
                        if item == playlist.current else ""
                    )

                    media_type = playlist.get_media_type(item)

                    print(
                        f"{i}. {item.title} - {item.artist}"
                        f" [{media_type}]{marker}"
                    )

                    print("   File:", item.filepath)

            input("\nPress Enter to return to menu...")

        elif choice == "4":
            title = input("Enter title to search: ")
            found = playlist.search(title)

            if found:
                print("Media found:", found.title, "-", found.artist)
                print("Type:", playlist.get_media_type(found))
                print("File:", found.filepath)

            else:
                print("Media not found.")

        elif choice == "5":
            playlist.play_current()

        elif choice == "6":
            playlist.next_track()

        elif choice == "7":
            playlist.previous_track()

        elif choice == "8":
            node = playlist.current_track()

            if node:
                print(f"Current: {node.title} - {node.artist}")
                print("Type:", playlist.get_media_type(node))
                print("File:", node.filepath)

            else:
                print("No", playlist.mode, "media selected.")

        elif choice == "9":
            print(playlist.sort_by_title())

        elif choice == "10":
            playlist.stop_audio()
            print("Playback stopped.")

        elif choice == "11":
            print("\n===== CHANGE MEDIA MODE =====")
            print("1. Audio Mode")
            print("2. Video Mode")

            mode_choice = input("Choose mode: ").strip()

            if mode_choice == "1":
                playlist.set_mode("Audio")

            elif mode_choice == "2":
                playlist.set_mode("Video")

            else:
                print("Invalid mode choice.")

        elif choice == "0":
            playlist.stop_audio()
            print("Exiting Music / Media Playlist Manager.")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()