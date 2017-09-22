import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.border.EmptyBorder;
import javax.swing.border.LineBorder;
import javax.swing.border.TitledBorder;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.text.DecimalFormat;
import java.text.NumberFormat;
/**
 * This function creates a GUI to load, display and modify the directory class.
 * @author maxmaguire
 *
 */
public class Practice extends JFrame {
    /**
     * Static final instance to hold donation constraint
     */
    private static final int DONATION_LIMIT = 10000000;
    /**
     * instance variable for romney list
     */
    private List<Contributor> romneyList = new ArrayList<Contributor>();
    /**
     * instance variable for Obama list
     */
    private List<Contributor> obamaList = new ArrayList<Contributor>();
    /**
     * instance variable for FN editor.
     */
    private JTextField firstNameEditor;
    /**
     * instance variable for LN editor.
     */
    private JTextField lastNameEditor;
    /**
     * instance variable for add Amount editor.
     */
    private JTextField AmountEditor;
    /**
     * instance variable for obama contribute button.
     */
    private JButton ObamaContribute;
    /**
     * instance variable for Romney contribute button
     */
    private JButton RomneyContribute;
    /**
     * instance variable for obama contribute List button.
     */
    private JButton ObamaContributeList;
    /**
     * instance variable for Romney contribute List button
     */
    private JButton RomneyContributeList;
    /**
     * instance variable for results editor.
     */
    private JTextArea resultsEditor;
    /**
     * Constructor for Directory Driver.
     * @param args input csv file.
     */
    public Practice(String[] args) {
        setBounds(100, 100, 825, 500);
        setTitle("Midterm Champaign Contribution Applications");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        JPanel mainPane = new JPanel();
        mainPane.setBorder(new EmptyBorder(5, 5, 5, 5));
        // Create panels
        FlowLayout flPanel1  = new FlowLayout(FlowLayout.CENTER, 5, 5);
        // initialize container 1
        JPanel panel1 = new JPanel();
        panel1.setBounds(10, 10, 805, 40);
        panel1.setLayout(flPanel1);
        // initialize container 2
        JPanel panel2 = new JPanel();
        panel2.setLayout(flPanel1);
        panel2.setBounds(10, 50, 805, 40);
        // initialize container 3
        JPanel panel3 = new JPanel();
        panel3.setLayout(flPanel1);
        panel3.setBounds(10, 100, 805, 40);
        // initialize container 1
        JPanel panel4 = new JPanel();
        panel4.setLayout(flPanel1);
        panel4.setBounds(10, 150, 805, 320);
        panel4.setLayout(null);
        mainPane.setLayout(null);
        // Create Buttons
        ObamaContribute      = new JButton("Contribute to Obama");
        RomneyContribute     = new JButton("Contribute to Romney");
        ObamaContributeList  = new JButton("List Obama Contributors");
        RomneyContributeList = new JButton("List Romney Contributors");
        // Create labels
        JLabel lblLastName  = new JLabel("Contributor Last Name:");
        JLabel lblFirstName = new JLabel("First Name:");
        JLabel lblAmount    = new JLabel("Amount:");

        // Define editor properties
        final int editTextSize1 = 8;
        firstNameEditor   = new JTextField();
        firstNameEditor.setColumns(editTextSize1);
        lastNameEditor    = new JTextField();
        lastNameEditor.setColumns(editTextSize1);
        AmountEditor    = new JTextField();
        AmountEditor.setColumns(editTextSize1);
        final int[] editTextSize3 = {60, 30, 670, 270};
        // define results properties
        resultsEditor = new JTextArea();
        resultsEditor.setBounds(editTextSize3[0], editTextSize3[1], editTextSize3[2], editTextSize3[3]);
        resultsEditor.setEditable(false);
        resultsEditor.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        resultsEditor.setLineWrap(true);
        resultsEditor.setWrapStyleWord(true);
        JScrollPane scroller = new JScrollPane(resultsEditor);
        scroller.setLocation(editTextSize3[0], editTextSize3[1]);
        scroller.setSize(editTextSize3[2] - 10, editTextSize3[3] - 10);
        scroller.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        // Populate panel1
        panel1.add(lblLastName);
        panel1.add(lastNameEditor);
        panel1.add(lblFirstName);
        panel1.add(firstNameEditor);
        panel1.add(lblAmount);
        panel1.add(AmountEditor);
        mainPane.add(panel1);
        // Populate panel2
        panel2.add(ObamaContribute);
        panel2.add(RomneyContribute);
        mainPane.add(panel2);
        // Populate panel3
        panel3.add(ObamaContributeList);
        panel3.add(RomneyContributeList);
        mainPane.add(panel3);
        // Populate panel4
        panel4.add(scroller);
        mainPane.add(panel4);
        // Add Action Listener to buttons
        // Add Action Listener to text fields [ENTER]
        ObamaContribute.addActionListener(new ObamaContributeActionListener());
        RomneyContribute.addActionListener(new RomneyContributeActionListener());
        ObamaContributeList.addActionListener(new ObamaContributeListActionListener());
        RomneyContributeList.addActionListener(new RomneyContributeListActionListener());
        // Set GUI handles visible
        setContentPane(mainPane);
        setVisible(true);
    }
    /**
     * Main function to construct GUI directory.
     * @param args filepath of csv file to initialize directory.
     */
    public static void main(String[] args) {
        // Read input csv file and return directory
        Practice pp = new Practice(args);
    }
    private class ObamaContributeActionListener implements ActionListener {
        /**
         * Action event for Add button listener.
         * @param event for button.
         */
        public void actionPerformed(ActionEvent event) {
            int donation = 0;
            if (firstNameEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a first Name before attempting to add a donar to the list");
                return;
            }
            if (lastNameEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a Last Name before attempting to add a donar to the list");
                return;
            }
            if (AmountEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a donation before attempting to add a donar to the list");
                return;
            }
            try {
                donation = Integer.parseInt(AmountEditor.getText());
            } catch (Exception e) {
                System.out.println(e.getMessage());
            }
            if (donation < 0 ) {
                resultsEditor.append("*** Contribution is must be greater than 0\n");
                return;
            }
            if (donation > DONATION_LIMIT) {
                resultsEditor.append("*** Contribution is too large ($ " + DONATION_LIMIT + " is the maximum allowd)\n");
                return;
            }
            Contributor donar = null;
            // Check if donar exists, if so update donation
            int prevdonation = 0;
            if (!obamaList.isEmpty()) {
                donar = SearchListforDonar(obamaList,firstNameEditor.getText(),lastNameEditor.getText());
                if (donar != null){
                    prevdonation = donar.getAmount();
                    obamaList.remove(donar);
                }
            }
            donar = new Contributor(firstNameEditor.getText(),lastNameEditor.getText(),donation,"obama");
            obamaList.add(donar);
            resultsEditor.append(donar.toString() + "\n");
            donar.setamount(donation + prevdonation);
            AmountEditor.setText(null);
            firstNameEditor.setText(null);
            lastNameEditor.setText(null);
            return;
        }
    } 
    private class RomneyContributeActionListener implements ActionListener {
        /**
         * Action event for Add button listener.
         * @param event for button.
         */
        public void actionPerformed(ActionEvent event) {
            int donation = 0;
            if (firstNameEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a first Name before attempting to add a donar to the list");
                return;
            }
            if (lastNameEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a Last Name before attempting to add a donar to the list");
                return;
            }
            if (AmountEditor.getText().isEmpty()) {
                resultsEditor.setText("Please enter a donation before attempting to add a donar to the list");
                return;
            }
            try{
                donation = Integer.parseInt(AmountEditor.getText());
            } catch(Exception e) {
                System.out.println(e.getMessage());
                return;
            }
            if (donation < 0 ) {
                resultsEditor.append("*** Contribution is must be greater than 0\n");
                return;
            }
            if (donation > DONATION_LIMIT) {
                resultsEditor.append("*** Contribution is too large ($ " + DONATION_LIMIT + " is the maximum allowd)\n");
                return;
            }
            Contributor donar = null;
            // Check if donar exists, if so update donation
            int prevdonation = 0;
            if (!romneyList.isEmpty()) {
                donar = SearchListforDonar(romneyList,firstNameEditor.getText(),lastNameEditor.getText());
                if (donar != null){
                    prevdonation = donar.getAmount();
                    romneyList.remove(donar);
                }
            }
            donar = new Contributor(firstNameEditor.getText(),lastNameEditor.getText(),donation,"romney");
            romneyList.add(donar);
            resultsEditor.append(donar.toString() + "\n");
            donar.setamount(donation + prevdonation);
            AmountEditor.setText(null);
            firstNameEditor.setText(null);
            lastNameEditor.setText(null);
            return;
        }
    } 
    private class ObamaContributeListActionListener implements ActionListener {
        /**
         * Action event for Add button listener.
         * @param event for button.
         */
        public void actionPerformed(ActionEvent event) {
            resultsEditor.setText(null);
            int totalContribution = 0;
            Collections.sort(obamaList, new Comparator<Contributor>() {
                public int compare(Contributor c1,Contributor c2) {
                    Integer c1_temp = c1.getAmount();
                    Integer c2_temp = c2.getAmount();
                    if (c2_temp.equals(c1_temp)) {
                        String c1_LName = c1.lastName;
                        String c2_LName = c2.lastName;
                        if (c2_temp.equals(c1_temp)) {
                            String c1_FName = c1.firstName;
                            String c2_FName = c2.firstName;
                            return c2_FName.compareTo(c1_FName);
                        }
                        return c2_LName.compareTo(c1_LName);
                    }
                    return c2_temp.compareTo(c1_temp);
                }
            });
            for (Contributor c : obamaList) {
                resultsEditor.append(c.toString() + "\n");
                totalContribution = totalContribution + c.getAmount();
            }
            resultsEditor.append("\n");
            resultsEditor.append("Total contribution for Obama : $ " + 
                    NumberFormat.getNumberInstance().format(totalContribution) + "\n");
            AmountEditor.setText(null);
            firstNameEditor.setText(null);
            lastNameEditor.setText(null);
            return;
        }
    } 
    private class RomneyContributeListActionListener implements ActionListener {
        /**
         * Action event for Add button listener.
         * @param event for button.
         */
        public void actionPerformed(ActionEvent event) {
            resultsEditor.setText(null);
            int totalContribution = 0;
            /*
            Collections.sort(romneyList, new Comparator<Contributor>() {
                public int compare(Contributor c1,Contributor c2) {
                    Integer c1_temp = c1.getAmount();
                    Integer c2_temp = c2.getAmount();
                    if (c2_temp.equals(c1_temp)) {
                        String c1_LName = c1.lastName;
                        String c2_LName = c2.lastName;
                        if (c2_temp.equals(c1_temp)) {
                            String c1_FName = c1.firstName;
                            String c2_FName = c2.firstName;
                            return c2_FName.compareTo(c1_FName);
                        }
                        return c2_LName.compareTo(c1_LName);
                    }
                    return c2_temp.compareTo(c1_temp);
                }
            });*/
            Collections.sort(romneyList);
            for (Contributor c : romneyList) {
                resultsEditor.append(c.toString() + "\n");
                totalContribution = totalContribution + c.getAmount();
            }
            resultsEditor.append("\n");
            resultsEditor.append("Total contribution for Romney : $ " + 
                    NumberFormat.getNumberInstance().format(totalContribution) + "\n");
            AmountEditor.setText(null);
            firstNameEditor.setText(null);
            lastNameEditor.setText(null);
            return;
        }
    } 
    public class Contributor implements Comparable<Contributor> {
        /**
         * Instance variable for first Name.
         */
        private String firstName;
        /**
         * Instance variable for last Name.
         */
        private String lastName;
        /**
         * Instance variable for Amount.
         */
        private int amount;
        /**
         * Instance variable for candidate.
         */
        private String candidate;
        /**
         * Constructs object with Last Name,First Name, Amount.
         * @param andrewId object.
         */
        public Contributor (String firstNameEntry, String lastNameEntry, int amountEntry, String candidateEntry) {
            // May be redundant
            if (firstNameEntry == null) {
                throw new IllegalArgumentException("Must add a first name");
            }
            // May be redundant
            if (lastNameEntry == null) {
                throw new IllegalArgumentException("Must add a last name");
            }
            // May be redundant
            if (candidateEntry == null) {
                throw new IllegalArgumentException("Must add a Candidate");
            }
            amount = amountEntry;
            lastName = lastNameEntry;
            firstName = firstNameEntry;
            candidate = candidateEntry;
        }
        /**
         * Returns Amount of contributor object.
         * @return amount.
         */
        public int getAmount() {
            return amount;
        }
        /**
         * Returns first name of contributor object.
         * @return firstName.
         */
        public String getFirstName() {
            return firstName;
        }
        /**
         * Returns last name of contributor object.
         * @return lastName.
         */
        public String getLastName() {
            return lastName;
        }
        /**
         * Returns candidate of contributor object.
         * @return candidate.
         */
        public String getCandidate() {
            return candidate;
        }
        /**
         * Set first name of contributor object.
         * @param s first name.
         */
        public void setFirstName(String s) {
            if (s == null) {
                throw new IllegalArgumentException("Cannot accept null string");
            }
            firstName = s;
        }
        public void setamount(int val ) {
            amount = val;
        }
        /**
         * Set last name of contributor object.
         * @param s last name.
         */
        public void setLastName(String s) {
            if (s == null) {
                throw new IllegalArgumentException("Cannot accept null string");
            }
            lastName  = s;
        }
        /**
         *
         */
        @Override
        public String toString() {
            String Namevar = lastName + ", " + firstName;
            return String.format("%-15s %40d\t\t%s",Namevar,amount,candidate);
        }
        @Override
        public int compareTo(Contributor o) {
            Integer c1_temp = this.getAmount();
            Integer c2_temp = o.getAmount();
            if (c2_temp.equals(c1_temp)) {
                String c1_LName = this.lastName;
                String c2_LName = o.lastName;
                if (c2_temp.equals(c1_temp)) {
                    String c1_FName = this.firstName;
                    String c2_FName = o.firstName;
                    return c2_FName.compareTo(c1_FName);
                }
                return c2_LName.compareTo(c1_LName);
            }
            return c2_temp.compareTo(c1_temp);
            // TODO Auto-generated method stub
            //return 0;
        }       
    }
    public Contributor SearchListforDonar(List<Contributor> candidateList,String firstName, String lastName) {
        for (Contributor c : candidateList ) {
            if (c.getFirstName().equals(firstName) & c.getLastName().equals(lastName)) {
                return c;
            }
        }
        return null;  
    }
}
