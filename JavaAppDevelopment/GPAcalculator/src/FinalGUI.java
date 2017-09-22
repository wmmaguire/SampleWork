import java.awt.Color;
import java.awt.FlowLayout;
import java.awt.Font;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Collections;
import java.util.Comparator;
import java.util.Date;
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
 * This function creates a GUI to load, display and modify the GPA data.
 * @author maxmaguire
 *
 */
public class FinalGUI extends JFrame {
    private final int[] UNIT_LIMITS = {0,99};
    /**
     * 
     */
    private final String[] SEASONS = {"Spring","Summer","Fall"};
    /**
     * instance variable for grade list
     */
    private List<FinalData> gradeList = new ArrayList<FinalData>();
    /**
     * instance variable for year editor.
     */
    private JTextField yearEditor;
    /**
     * instance variable for semester editor.
     */
    private JTextField semesterEditor;
    /**
     * instance variable for add courseNameEditor editor.
     */
    private JTextField courseNameEditor;
    /**
     * instance variable for units editor.
     */
    private JTextField unitsEditor;
    /**
     * instance variable for gpa editor.
     */
    private JTextField gpaEditor;
    /**
     * instance variable for grade editor.
     */
    private JTextField gradeEditor;
    /**
     * instance variable for results editor.
     */
    private JTextField errorEditor;
    /**
     * instance variable for results editor.
     */
    private JTextArea resultsEditor;
    /**
     * instance variable for addGrade button.
     */
    private JButton addGradeButton;
    /**
     * instance variable for season.
     */
    private static String season;
    
    public FinalGUI(String[] args) {
        setBounds(100, 100, 825, 500);
        setTitle("08-671 Programming Exam");
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        JPanel mainPane = new JPanel();
        mainPane.setBorder(new EmptyBorder(5, 5, 5, 5));
        Calendar rightNow = Calendar.getInstance();
        switch (rightNow.MONTH) {
        case 0:
            season = SEASONS[0];
            break;
        case 1:
            season = SEASONS[0];
            break;
        case 2:
            season = SEASONS[0];
            break;
        case 3:
            season = SEASONS[0];
            break;
        case 4:
            season = SEASONS[1];
            break;
        case 5:
            season = SEASONS[1];
            break;
        case 6:
            season = SEASONS[1];
            break;
        case 7:
            season = SEASONS[1];
            break;
        case 8:
            season = SEASONS[2];
            break;
        case 9:
            season = SEASONS[3];
            break;
        case 10:
            season = SEASONS[3];
            break;
        case 11:
            season = SEASONS[3];
            break;
    }
        // Create panels
        FlowLayout flPanel1  = new FlowLayout(FlowLayout.CENTER, 5, 5);
        FlowLayout flPanel2  = new FlowLayout(FlowLayout.CENTER, 90, 5);
        //TitledBorder border1 = new TitledBorder("Year");
        // initialize container 1
        JPanel panel1 = new JPanel();
        panel1.setBounds(10, 10, 805, 20);
        panel1.setLayout(flPanel2);
        // initialize container 2
        JPanel panel2 = new JPanel();
        panel2.setLayout(flPanel1);
        panel2.setBounds(10, 30, 805, 30);
        // initialize container 3
        JPanel panel3 = new JPanel();
        panel3.setLayout(flPanel1);
        panel3.setBounds(10, 70, 805, 30);
        // initialize container 4
        JPanel panel4 = new JPanel();
        panel4.setLayout(flPanel1);
        panel4.setBounds(10, 110, 805, 30);
        // initialize container 1
        JPanel panel5 = new JPanel();
        panel5.setLayout(flPanel1);
        panel5.setBounds(10, 150, 805, 320);
        panel5.setLayout(null);
        mainPane.setLayout(null);
        // Create Buttons
        addGradeButton      = new JButton("Add Grade");
        // Define editor properties
        final int editTextSize1 = 8;
        yearEditor   = new JTextField("2017");
        yearEditor.setColumns(editTextSize1);
        semesterEditor    = new JTextField(season);
        semesterEditor.setColumns(editTextSize1);
        final int editTextSize2 = editTextSize1*2;
        courseNameEditor    = new JTextField();
        courseNameEditor.setColumns(editTextSize2);
        unitsEditor    = new JTextField();
        unitsEditor.setColumns(editTextSize1);
        gradeEditor    = new JTextField();
        gradeEditor.setColumns(editTextSize1);
        gpaEditor    = new JTextField();
        gpaEditor.setEditable(false);
        gpaEditor.setColumns(editTextSize1);
        final int editTextSize3 = 50;
        errorEditor    = new JTextField();
        errorEditor.setEditable(false);
        errorEditor.setColumns(editTextSize3);
        errorEditor.setForeground(Color.RED);
        final int[] editTextSize4 = {60, 30, 670, 270};
        // define results properties
        resultsEditor = new JTextArea();
        resultsEditor.setBounds(editTextSize4[0], editTextSize4[1], editTextSize4[2], editTextSize4[3]);
        resultsEditor.setEditable(false);
        resultsEditor.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        resultsEditor.setLineWrap(true);
        resultsEditor.setWrapStyleWord(true);
        resultsEditor.setText(String.format(" %-7s %-7s  %-38s  %-10s %10s %10s\n",
                "Year","Semester","Course","Units","Grade","Points"));
        JScrollPane scroller = new JScrollPane(resultsEditor);
        scroller.setLocation(editTextSize4[0], editTextSize4[1]);
        scroller.setSize(editTextSize4[2] - 10, editTextSize4[3] - 10);
        scroller.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        // Populate panel1
        panel1.add(new JLabel("Year"));
        panel1.add(new JLabel("Semester"));
        panel1.add(new JLabel("Course Name"));
        panel1.add(new JLabel("Units"));
        panel1.add(new JLabel("Grade"));
        mainPane.add(panel1);
        // Populate panel2
        panel2.add(yearEditor);
        panel2.add(semesterEditor);
        panel2.add(courseNameEditor);
        panel2.add(unitsEditor);
        panel2.add(gradeEditor);
        mainPane.add(panel2);
        // Populate panel3
        panel3.add(addGradeButton);
        panel3.add(new JLabel("Grade Point Average"));
        panel3.add(gpaEditor);
        mainPane.add(panel3);
        // Populate panel4
        panel4.add(errorEditor);
        mainPane.add(panel4);
        // Populate panel5
        panel5.add(scroller);
        mainPane.add(panel5);
        // Add Action Listener to buttons
        // Add Action Listener to text fields [ENTER]
        addGradeButton.addActionListener(new addGradeActionListener());
      //  RomneyContribute.addActionListener(new RomneyContributeActionListener());
      //  ObamaContributeList.addActionListener(new ObamaContributeListActionListener());
      //  RomneyContributeList.addActionListener(new RomneyContributeListActionListener());
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
        FinalGUI fg = new FinalGUI(args);
    }
    /**
     * 
     * @author maxmaguire
     *
     */
    private class addGradeActionListener implements ActionListener {
        /**
         * 
         */
        public void actionPerformed(ActionEvent event) {
            resultsEditor.setText(String.format(" %-7s %-7s  %-38s  %-10s %10s %10s\n",
                    "Year","Semester","Course","Units","Grade","Points"));
            int unitval = 0;
            int yearval = 0;
            // Make sure that grade Editor is an entry
            if (yearEditor.getText().isEmpty()) {
                errorEditor.setText("Please enter a year before making entry");
                return;
            }
            // Make sure that course name is an entry
            if (courseNameEditor.getText().isEmpty()) {
                errorEditor.setText("Please type a course name before making entry");
                return;
            }
            // Make sure that units value is an entry
            if (unitsEditor.getText().isEmpty()) {
                errorEditor.setText("Please enter a unit number before making entry");
                return;
            }
            try{
                unitval = Integer.parseInt(unitsEditor.getText());
            } catch (Exception e) {
                errorEditor.setText("illegal unit value entry: " + unitval);
                return;
            }
            if (unitval < UNIT_LIMITS[0] || unitval > UNIT_LIMITS[1]) {
                errorEditor.setText("units must be an integer value between 0-99 ");
            }
            // Make sure that course name is an entry
            if (semesterEditor.getText().isEmpty()) {
                errorEditor.setText("Please enter a Semester before making entry");
                return;
            }
            season = semesterEditor.getText();
            if (!(season.equals(SEASONS[0]) || season.equals(SEASONS[1]) || season.equals(SEASONS[2]))) {
                errorEditor.setText("invalid Season entry.  Must be Fall, Spring or Summer");
                return;
            }
            // Make sure that grade Editor is an entry
            if (gradeEditor.getText().isEmpty()) {
                errorEditor.setText("Please enter a letter grade before making entry");
                return;
            }
            // Make sure that Grade value lie between A-F
            String letterGrade = gradeEditor.getText();
            if (!(letterGrade.equalsIgnoreCase("A") || letterGrade.equalsIgnoreCase("B") ||
                    letterGrade.equalsIgnoreCase("C") || letterGrade.equalsIgnoreCase("D") ||
                    letterGrade.equalsIgnoreCase("D"))) {
                errorEditor.setText("illegal grade entry: must be between A-F");
                return;
            }
            
            try{
                yearval = Integer.parseInt(yearEditor.getText());
            } catch (Exception e){
                errorEditor.setText("illegal year value entry: " + yearval);
                return;
            }
            FinalData fd = new FinalData(yearval,season,courseNameEditor.getText(),unitval,letterGrade);
            gradeList.add(fd);
            Collections.sort(gradeList);
            for (FinalData fd_temp : gradeList) {
                resultsEditor.append(fd_temp.toString());
            }
            gpaEditor.setText(String.format("%1.2f", computeGPA()));
            return;
        }
        public double computeGPA() {
            double totalpoints = 0;
            double totalunits  = 0;
            for (FinalData fd : gradeList) {
                totalpoints = totalpoints + fd.getPoints();
                totalunits  = totalunits + fd.getUnits();
            }
            return totalpoints/totalunits;
        }
    }
}