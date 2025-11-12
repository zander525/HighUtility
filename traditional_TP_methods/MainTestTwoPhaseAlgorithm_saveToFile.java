package traditional_TP;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.URL;

import traditional_TP.AlgoTwoPhase;
import traditional_TP.ItemsetsTP;
import traditional_TP.UtilityTransactionDatabaseTP;

/**
 * Example of how to use the TWOPhase Algorithm in source code.
 * @author Philippe Fournier-Viger, 2010
 */
public class MainTestTwoPhaseAlgorithm_saveToFile {

	public static void main(String [] arg) throws IOException{
		
		String input = fileToPath("new_DB_Utility.txt");
		String output = "D:/Eclipse/highUtility/src/two_phase/output.txt";

		double utilityFactor = 1; 
		
		// Loading the database into memory
		UtilityTransactionDatabaseTP database = new UtilityTransactionDatabaseTP();
		database.loadFile(input);
		
		//int min_utility = (int) (database.size() * utilityFactor);
		int min_utility = 20;
				
		// Applying the Two-Phase algorithm
		AlgoTwoPhase twoPhase = new AlgoTwoPhase();
		ItemsetsTP highUtilityItemsets = twoPhase.runAlgorithm(database, min_utility);
		
		highUtilityItemsets.saveResultsToFile(output, database.getTransactions().size());

		twoPhase.printStats();

	}

	public static String fileToPath(String filename) throws UnsupportedEncodingException{
		URL url = MainTestTwoPhaseAlgorithm_saveToFile.class.getResource(filename);
		 return java.net.URLDecoder.decode(url.getPath(),"UTF-8");
	}
}
