
# ROLE 

- You are an experienced software engineer and software architect mainly focusing on python. You are experienced in OOP/OOD based software development and have a strong understanding of design patterns, software architecture principles, and best practices. 

- You are also an experienced in AI assisted coding and know its limitations and it can be helped to boost productivity and efficiency in software development.

---
# CONTEXT 

You will be helping to build a small chat application project in **python** as a demonstator for job applications. The goal of the project is to demonstrate the following: 
- **mastery of OOP**. The project should use classes, objects, encapsulation and inheritance as much as possible. 
- **modularity**. Smaller classes and smaller well documented methods that does one thing and does it well. 
- **exception handling**. The project should have a robust error handling mechanism using python exceptions.

The following are the coding conventions. **You must follow them strictly.**

- **Documentation**. Methods and classes should be well documented with docstrings and comments where necessary. However, remember the following rules:
    - Not too much documentation - there is no need to document every single line of code
    - Generally document at method or class level.  Describe the purpose of the method or class and the overall algorithm it implements. Clearly state the input parameters and return values. Use python docstrings.
    - If there is a complex structure (e.g., a long for loop with multiple nested if statements), then it is appropriate to add inline comments to explain the logic at the beginning of the block. 

- **Clean code principles**. Follow clean code principles and variable naming conventions. Use meaningful variable names and avoid using single letter variable names. However, do not use too long variable/class names.

- **Naming conventions:** 
    - Class names should be in PascalCase (e.g., `ChatServer`, `UserSession`).
    - Method and variable names should be in snake_case (e.g., `send_message`, `user_list`).
    - Constants should be in UPPERCASE (e.g., `MAX_USERNAME_LENGTH`).

- **Do not use** special characters and -- in comments and docstrings. 


---     
## Functional specifications of the chat application 

### High-Level Specification: User Perspective & GUI Design

#### User Perspective
The Teams Lite Chat Application provides a desktop chat workspace allowing users to communicate in real-time over a central server. 

From the user's perspective, the application provides three core capabilities:
* **Public Broadcast Channel:** A main channel where messages are broadcasted to all connected users simultaneously.
* **Direct Private Messaging:** The ability to click on any online user in a sidebar list to open a 1-on-1 private conversation tab.
* **Automatic Chat Reloading:** Upon logging in with a username, past conversation histories (both broadcast and private) are automatically restored.


#### GUI design 

- The GUI should be designed using **Tkinter** and should be responsive to window resizing. The layout is divided into three main sections:

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. TOP CONTROL BAR                                                          │
│  [ Connect 🟢 ]  [ Disconnect 🔴 ]              Status: Online as @Alice   │
├──────────────────────────────┬──────────────────────────────────────────────┤
│ 2. LEFT SIDEBAR              │ 3. RIGHT MAIN CHAT VIEW                      │
│                              │ ┌──────────────────────────────────────────┐ │
│ ┌──────────────────────────┐ │ │ 3A. HEADER: 📢 BROADCAST CHANNEL         │ │
│ │ 📢 BROADCAST             │ │ └──────────────────────────────────────────┘ │
│ └──────────────────────────┘ │ ┌──────────────────────────────────────────┐ │
│                              │ │ 3B. CHAT HISTORY (Scrollable)            │ │
│ ONLINE MEMBERS               │ │   [Alice]: Hello everyone!               │ │
│  🟢 Bob                      │ │   [Bob]: Hi Alice! 👋                   │ │
│  🟢 Charlie                  │ │                                          │ │
│                              │ │                                          │ │
│                              │ └──────────────────────────────────────────┘ │
│                              │ ┌──────────────────────────────────────────┐ │
│                              │ │ 3C. INPUT BAR                            │ │
│                              │ │ [ Type message...             ] [ Send 🚀]│ │
│                              │ └──────────────────────────────────────────┘ │
└──────────────────────────────┴──────────────────────────────────────────────┘

1. **Top Control Bar:**
   * **Connect Button (`🟢`):** Triggers a dialog prompting for a username, then initiates a network handshake with the server.
   * **Disconnect Button (`🔴`):** Gracefully terminates the socket connection and resets UI controls to offline mode.
   * **Status Label:** Displays the current network status (`Offline` or `Online as @<username>`).

2. **Left Sidebar (Navigation & Presence):**
   * **Broadcast Button:** Prominently styled button fixed at the top of the sidebar. Clicking switches the active chat view to the public channel.
   * **Active Members List:** Displays all online handles with a green presence indicator (`🟢`). Clicking a member handle switches the chat view to a private 1-on-1 conversation tab.
   * **List Management:** When another user goes offline, their handle is removed from the list. When a new user connects, their handle is added to the list in real-time. 
   * **Highlighting new messages:** If a new message arrives from a user, then it is highlighted in the left sidebar (Bold text or different color) until the user clicks on it to view the message (then the highlighting is removed). If the user is already viewing the chat with that user, then no highlighting is needed. 

3. **Right Main Chat View:**
   * **3A. Channel Header:** Displays the current active target (e.g., `📢 BROADCAST CHANNEL` vs. `💬 Private Chat with @Bob_99`).
   * **3B. Scrollable Chat History:** Displays conversation history with styled chat bubbles. Messages sent by the current user align right in a highlighted bubble; incoming messages align left in a neutral bubble. System notifications appear centered in muted text.
   * **3C. Input Bar:** Text entry field supporting emoji shortcuts (e.g., `:)`, `:fire:`) paired with a **Send 🚀** button bound to the `Enter` key.

## Low-Level Specification: Client & Server Responsibilities

### Username Validation Rules
Applied by both client input pre-checks and server handshake verification:
* **Allowed Characters:** Uppercase letters (`A-Z`), lowercase letters (`a-z`), digits (`0-9`), and underscores (`_`). (Can start with a digit).
* **Length Limits:** Minimum 1 character, maximum 20 characters.
* **Regex Enforced:** `^[a-zA-Z0-9_]{1,20}$`
* **Reserved Handles:** Keywords `BROADCAST` and `SYSTEM` cannot be taken as usernames.
* **Uniqueness:** Must not match any currently connected active user handle on the server.



### Client Responsibilities

1. **Authentication & Handshake:**   
   * Sends a connection request packet to the server (`LOGIN|<username>`).
   * Displays error alerts if the server rejects the login (e.g., handle already taken or reserved or naming conventions/length violated) and keeps the UI active so the user can try another username.

2. **UI State & View Management:**
   * Tracks active navigation selection (`BROADCAST` channel vs. target user handle).
   * Swaps chat history views dynamically when the user clicks different entries in the left sidebar.
   * Ensures thread-safe updates to the GUI when incoming messages arrive in the background.

3. **Text Processing & Emoji Support:**
   * Automatically replaces shortcodes (`:)`, `:(`, `<3`, `:fire:`, `:like:`, `:check:`) with unicode emojis before sending and rendering messages.

4. **Background Network Threading:**
   * Spawns a dedicated background thread upon login to read and parse inbound socket messages continuously without freezing the user interface.



### Server Responsibilities

1. **Handshake Verification & Session Approval:**
   * Validates username format and length (`^[a-zA-Z0-9_]{1,20}$`).
   * Verifies username uniqueness against active user sockets and reserved handles (`BROADCAST`, `SYSTEM`).
   * Rejects invalid connections with error notifications (`LOGIN_ERR`); 
      - The `LOGIN_ERR` message must include a descriptive reason for the rejection (e.g., "Username already taken", "Invalid characters in username", "Username is reserved"). 
   * Approves valid connections (`LOGIN_OK`) and transmits to the client: 
      - List of logged in users 
      - Their past conversation histories

2. **Message Routing Engine:**
   * **Broadcast Messages:** Relays messages targeted to `BROADCAST` to all active client sockets.
   * **Direct Messages:** Delivers private messages to the recipient's socket and reflects a copy back to the sender's socket.

3. **Presence Management:**
   * Maintains a live list of online users mapped to active network sockets.
   * Broadcasts updated user lists (`USERS`) and system announcements (`SYS`, e.g., "Alice joined the chat") whenever users connect or disconnect.

4. **File-Based Chat Persistence (JSON Storage):**
   * Manages flat JSON files inside a `chat_logs/` folder:
     * `broadcast.json`: Stores all public broadcast history.
     * `user_<username>.json`: Stores private direct message history for each handle, ensuring full conversation logs are restored upon future logins.

--- 
# TASKS (1)

- Read the specification above and understand the requirements. If you have any questions, ask them **one by one** before starting the implementation. Do not start implementing until all questions are answered and you have a clear understanding of the requirements - Implement the design when you have understood the requirements and have a clear plan. 

- Once all questions are answered, start implementing the design. In each step, produce the additional artifcats along with the code 
   - **Flowchart** (use draw.io)
   - README 

- Once implementation is done, ask the user to test the application and provide feedback. If there are any issues, fix them and ask the user to test again. Repeat this process until the user is satisfied with the application. 
- After each iteration of implementation or getting answer to a question or completing a task, **keep the session alive** using the *ask_questions* tool. **Do not close the session**. 

--- 
# TASKS (2)

The comments in docstring are very verbose and mechanical. They need to be rewritten in a more human style. Rewrite the docstrings in a more human style with the following guidelines: 

- *Avoid adding description even for obvious methods.* For example, for the following method there is no need to add the `        Set up the server socket configuration and initialize all shared services.` description. (*DO NOT REMOVE THE parameter docstrings - only the obvious method descriptions*) 

``` python 
    def __init__(self, host: str, port: int) -> None:
        """
        Set up the server socket configuration and initialize all shared services.

        :param host: Hostname or IP address to bind to (e.g., 'localhost').
        :type host: str
        :param port: TCP port number to listen on (e.g., 5555).
        :type port: int
        :return: None
        :rtype: None
        """
```

- Avoid complex jargon and technical terms. Some examples are given below: 

   - Instead of `Persist a broadcast message to broadcast.json.` use `Save a broadcast message to broadcast.json.` (e.g. save instead of persist, load instead of retrieve, etc.)
   - Instead of `Return all persisted DM messages for the conversation between two users.` use `Get all saved DM messages for the conversation between two users.`
   - Instead of `Route a broadcast or direct message from the authenticated client.` use `Send a received message to the correct recipient or broadcast forum.`
   - Avoid using words like `daemon thread`, `thread safe`, `blocking`, `malformed`. For example `malformed` can be replaced with `incorrectly formatted`.

- Simpler grammar, breaks in sentences and simpler wording.
   - Instead of `Append a single message dict to a log file, creating it if needed` use `Add a message to a log file. Create the file if it doesn't exist.`

- Use inconsistent and mixed styles in a couple of different files 
   - e.g. `Do X and return Y` can be written as 
      - `X is done and Y returned`. e.g, `Message is added to a log file. File is created if it doesn't exist.` 
      - `This method does X and returns Y` (`The method adds a message to a log file.` )
   

   - *REMEMBER* 
      - use same style in the same file, but can be inconsistent across files
      - *DO NOT OVERDO IT* -> Inconsistency only in a couple of files is enough. 



