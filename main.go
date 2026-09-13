package main

import (
	"fmt"
	"os"
	"os/exec"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

// Styles
var (
	baseStyle = lipgloss.NewStyle().BorderStyle(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("240"))
	
	highlightStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#00FFCC")).Bold(true)
	titleStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF0055")).Bold(true).Padding(0, 1)
	subTitleStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF9900")).Bold(true)
	dimStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))

	logoAscii = `
 ▄▄▄▄    ▄████▄   ██▀███   ██████ ▓█████  ██▀███   ██ ▄█▀▓█████  ██▀███  
▓█████▄ ▒██▀ ▀█  ▓██ ▒ ██▒▒██    ▒ ▓█   ▀ ▓██ ▒ ██▒ ██▄█▒ ▓█   ▀ ▓██ ▒ ██▒
▒██▒ ▄██▒▓█    ▄ ▓██ ░▄█ ▒░ ▓██▄   ▒███   ▓██ ░▄█ ▒▓███▄░ ▒███   ▓██ ░▄█ ▒
▒██░█▀  ▒▓▓▄ ▄██▒▒██▀▀█▄    ▒   ██▒▒▓█  ▄ ▒██▀▀█▄  ▓██ █▄ ▒▓█  ▄ ▒██▀▀█▄  
░▓█  ▀█▓▒ ▓███▀ ░░██▓ ▒██▒▒██████▒▒░▒████▒░██▓ ▒██▒▒██▒ █▄░▒████▒░██▓ ▒██▒
`
	avatarAscii = `
       .-------.
      /   >_    \
     |  o    o   |
      \  '--'   /
       '-------'
`
)

type tool struct {
	name        string
	branch      string
	description string
	scriptPath  string
}

type model struct {
	tools  []tool
	cursor int
	width  int
	height int
	quitting bool
	selected *tool
}

func initialModel() model {
	return model{
		tools: []tool{
			{
				name:        "berserker (Log Correlation)",
				branch:      "Void",
				description: "Cross-Service Log Correlation Engine.\nIt auto-sniffs log formats (JSON, ISO8601, Bracket, Syslog),\nstandardizes chaotic logs into strict LogEntry formats,\nand instantly builds a relative-time correlation timeline\nacross different services based on shared transaction identifiers.",
				scriptPath:  "digger/digger.py",
			},
			{
				name:        "griffith (CI/CD Parser)",
				branch:      "griffith",
				description: "CI/CD Pipeline Error Summarizer.\nAuto-discovers broken CI/CD pipelines via the public GitHub API\nand downloads the raw logs. It is designed to extract\nhuman-readable error summaries from massive 500+ line pipeline breakages.",
				scriptPath:  "cicd_parser/parser.py",
			},
			{
				name:        "GodsHand (LLM Sandbox)",
				branch:      "conrad",
				description: "Local LLM Sandbox & Agent Manager.\nRuns a local LLM strictly within the terminal sandbox and\nevaluates the output of two sub-agents against specific rule sets,\nmonitored by a larger overarching model.",
				scriptPath:  "llm_sandbox/sandbox.py",
			},
			{
				name:        "Exit Toolkit",
				branch:      "",
				description: "Safely exit the Berserker TUI shell.",
				scriptPath:  "",
			},
		},
	}
}

func (m model) Init() tea.Cmd {
	return nil
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q", "esc":
			m.quitting = true
			return m, tea.Quit
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
		case "down", "j":
			if m.cursor < len(m.tools)-1 {
				m.cursor++
			}
		case "enter", " ":
			m.selected = &m.tools[m.cursor]
			m.quitting = true
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m model) View() string {
	if m.width == 0 {
		return "Initializing..."
	}

	leftWidth := m.width / 3
	rightWidth := m.width - leftWidth - 4
	if rightWidth < 10 { // Terminal too small safety fallback
		return "Terminal too small."
	}

	// LEFT COLUMN PANELS
	welcomeBox := baseStyle.Width(leftWidth).Render(
		fmt.Sprintf("%s\n%s", highlightStyle.Render("Welcome to Berserker Toolkit!"), time.Now().Format("15:04:05")),
	)
	
	avatarBox := baseStyle.Width(leftWidth).Height(10).Align(lipgloss.Center).Render(
		titleStyle.Render(avatarAscii),
	)

	controlsBox := baseStyle.Width(leftWidth).Render(
		subTitleStyle.Render("--- Controls ---") + "\n" +
			dimStyle.Render("j/k") + " or " + dimStyle.Render("up/down") + " to navigate\n" +
			dimStyle.Render("enter") + " to select\n" +
			dimStyle.Render("q") + " or " + dimStyle.Render("esc") + " to exit",
	)

	leftCol := lipgloss.JoinVertical(lipgloss.Left, welcomeBox, avatarBox, controlsBox)

	// RIGHT COLUMN PANELS
	logoBox := baseStyle.Width(rightWidth).Align(lipgloss.Center).Render(
		titleStyle.Render(logoAscii),
	)

	// Menu options
	var menuItems string
	for i, t := range m.tools {
		cursor := "  "
		style := lipgloss.NewStyle()
		if m.cursor == i {
			cursor = "➤ "
			style = highlightStyle
		}
		menuItems += style.Render(fmt.Sprintf("%s%s", cursor, t.name)) + "\n"
	}
	
	menuBox := baseStyle.Width(rightWidth).Height(12).Render(
		subTitleStyle.Render("Explore the Toolkit") + "\n" +
			dimStyle.Render("Use arrow keys to navigate and hit <Enter> to launch a tool.") + "\n\n" +
			menuItems,
	)

	detailsBox := baseStyle.Width(rightWidth).Height(7).Render(
		subTitleStyle.Render(m.tools[m.cursor].name) + "\n" +
			lipgloss.NewStyle().Foreground(lipgloss.Color("228")).Render("Branch: "+m.tools[m.cursor].branch) + "\n\n" +
			m.tools[m.cursor].description,
	)

	rightCol := lipgloss.JoinVertical(lipgloss.Left, logoBox, menuBox, detailsBox)

	// Final assembly
	return lipgloss.JoinHorizontal(lipgloss.Top, leftCol, rightCol)
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())
	m, err := p.Run()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	finalModel := m.(model)
	if finalModel.selected == nil || finalModel.selected.name == "Exit Toolkit" {
		fmt.Println("Goodbye!")
		return
	}

	// Execution
	scriptPath := finalModel.selected.scriptPath
	branchName := finalModel.selected.branch

	if _, err := os.Stat(scriptPath); os.IsNotExist(err) {
		fmt.Printf("\n🚧 [Warning] The logic for this tool is missing.\n")
		fmt.Printf("Please make sure the '%s' branch has been merged into main!\n\n", branchName)
		return
	}

	cmd := exec.Command("./venv/bin/python", scriptPath)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err = cmd.Run()
	if err != nil {
		fmt.Printf("\n❌ Process finished with error: %v\n", err)
	}
}
