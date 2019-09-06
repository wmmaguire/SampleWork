import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.Random;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;
import javax.swing.border.EmptyBorder;

/**
 * Thread driven Whack-a-Mole Game.
 * @author Max Maguire
 */
public class Game implements ActionListener {
    /**
     * Instance Variable Time Counter.
     */
    private int counter = 0;
    /**
     * Instance variable Buttons where moles pop out.
     */
    private JButton[] buttons;
    /**
     * Instance variable Timer to indicate the time left in a given game.
     */
    private JTextField timeEditor;
    /**
     * Instance variable Score indicator.
     */
    private JTextField scoreEditor;
    /**
     * Instance variable Button to start a new game.
     */
    private JButton startButton;
    /**
     * Instance variable Color to indicate a mole button.
     */
    private static final Color ON_COLOR  = Color.GREEN;
    /**
     * Instance variable Color to indicate an empty button.
     */
    private static final Color OFF_COLOR = Color.LIGHT_GRAY;
    /**
     * Instance variable Text to indicate an empty button.
     */
    private static final String OFF_TEXT = "   ";
    /**
     * Instance variable Text to indicate a mole button.
     */
    private static final String ON_TEXT  = ":-p";
    /**
     * Instance variable Color to indicate when a mole is hit.
     */
    private static final Color HIT_COLOR = Color.RED;
    /**
     * Instance variable Text to indicate when a mole is hit.
     */
    private static final String HIT_TEXT = "X-(";
    /**
     * Instance variable Game duration (20s).
     */
    private static final int GAME_DURATION = 20;
    /**
     * Constructor.
     * @param numLights number of lights using buttons
     */
    public Game(int numLights) {
        Font font = new Font(Font.MONOSPACED, Font.BOLD, 14);
        JFrame mainframe = new JFrame("Whack-a-mole Sample GUI");
        JPanel mainPane = new JPanel();
        mainPane.setBorder(new EmptyBorder(5, 5, 5, 5));
        mainframe.setSize(830, 430);
        mainframe.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        mainframe.setLayout(null);
        // Initialize control pane with components
        JPanel cntrlpane = new JPanel();
        cntrlpane.setBounds(5, 5, 820, 30);
        cntrlpane.setLayout(new FlowLayout(FlowLayout.CENTER, 5, 5));
        startButton = new JButton("Start");
        startButton.addActionListener(new StartActionListener());
        JLabel lblTimeLeft  = new JLabel("Time Left:");
        JLabel lblScore     = new JLabel("Score:");
        final int editTextSize1 = 6;
        timeEditor   = new JTextField();
        timeEditor.setColumns(editTextSize1);
        timeEditor.setEditable(false);
        scoreEditor  = new JTextField();
        scoreEditor.setColumns(editTextSize1);
        scoreEditor.setEditable(false);
        cntrlpane.add(startButton);
        cntrlpane.add(lblTimeLeft);
        cntrlpane.add(timeEditor);
        cntrlpane.add(lblScore);
        cntrlpane.add(scoreEditor);
        // Initialize button pane
        JPanel btnpane = new JPanel();
        btnpane.setBounds(5, 50, 820, 400);
        buttons = new JButton[numLights];
        for (int i = 0; i < buttons.length; i++) {
            // set every button to default state
            buttons[i] = new JButton(OFF_TEXT);
            buttons[i].setBackground(OFF_COLOR);
            buttons[i].setFont(font);
            buttons[i].setOpaque(true);
            buttons[i].setName("button_" + i);
            buttons[i].addActionListener(this);
            btnpane.add(buttons[i]);
        }
        mainframe.add(cntrlpane);
        mainframe.add(btnpane);
        mainframe.setVisible(true);
    }
    /**
     * Main method used to construct game with 100 lights.
     * @param args not used.
     */
    public static void main(String[] args) {
        int numLights    = 36;
        new Game(numLights);
    }
    /**
     * Runnable class for each button thread.
     * @author maxmaguire
     *
     */
    public class ButtonRunnable implements Runnable {
        // unique state per runnable instance
        /**
         * Instance variable of button.
         */
        private JButton myButton;
        /**
         * Constructor with button to start random on/off sequence.
         * @param button component to launch new runnable.
         */
        public ButtonRunnable(JButton button) {
            myButton = button;
        }
        /**
         * Implementation of run method of ButtonRunnable Interface.
         */
        @Override
        public void run() {
            Thread myThread = Thread.currentThread();
            int randTime;
            Random random = new Random();
            try {
                while (counter > 0) {
                    randTime = (random.nextInt(4) + 1) * 1000;
                    synchronized (myButton) {
                        myButton.setText(ON_TEXT);
                        myButton.setBackground(ON_COLOR);
                    }
                        Thread.sleep(randTime);
                    synchronized (myButton) {
                        myButton.setText(OFF_TEXT);
                        myButton.setBackground(OFF_COLOR);
                    }
                    randTime = (random.nextInt(4) * 500) + 2000;
                    Thread.sleep(randTime);
               }
            } catch (InterruptedException e) {
                System.out.println(myThread.getName() + ": Interrupted\n");
                System.out.println(e.getMessage());
            }
        }
    }
    /**
     * Nested class that extends Thread.
     * @author Max Maguire
     */
    private class TimerThread extends Thread {
        /**
         * Timer thread method.
         * used to control the state of the game.
         */
        @Override
        public void run() {
            timeEditor.setText(String.format("%d", counter));
            scoreEditor.setText(null);
            startButton.setEnabled(false);
            while (counter > 0) {
                try {
                    Thread.sleep(1000);
                    counter  = counter - 1;
                    timeEditor.setText(String.format("%d", counter));
                } catch (InterruptedException e) {
                    throw new AssertionError(e);
                }
            }
            try {
                Thread.sleep(5000);
            } catch (InterruptedException e) {
                throw new AssertionError(e);
            }
            startButton.setEnabled(true);
        }
    }
    /**
     * Action listener that reacts to start button press.
     * @author maxmaguire
     */
    private class StartActionListener implements ActionListener {
        @Override
        public void actionPerformed(ActionEvent e) {
            // TODO Auto-generated method stub
            counter = GAME_DURATION;
            Thread gameOn = new TimerThread();
            gameOn.start();
            for (int i = 0; i < buttons.length; i++) {
                ButtonRunnable r = new ButtonRunnable(buttons[i]);
                Thread t = new Thread(r);
                t.setName("button" + i);
                t.start();
            }
            scoreEditor.setText(null);
            }
    }
    /**
     * Action Listener to Game class for button press.
     * Used to determine if button pressed was a mole or not.
     * If it was, score will be incremented.
     */
    @Override
    public void actionPerformed(ActionEvent e) {
        // TODO Auto-generated method stub
        JButton buttonPressed = (JButton) e.getSource();
        int gametime = Integer.parseInt(timeEditor.getText());
        synchronized (buttonPressed) {
            if (buttonPressed.getBackground() == ON_COLOR & gametime > 0) {
                if (scoreEditor.getText().isEmpty()) {
                    scoreEditor.setText("1");
                    return;
                }
                String oldScore = scoreEditor.getText();
                int newScore = Integer.valueOf(oldScore) + 1;
                scoreEditor.setText(String.format("%d", newScore));
                buttonPressed.setBackground(HIT_COLOR);
                buttonPressed.setText(HIT_TEXT);
            }
        }
    }
}
