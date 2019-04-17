/*
A KBase module: mightymorphingmodels
*/

module mightymorphingmodels {
    /*
        Insert your typespec information here.
    */
    typedef structure {
    	string fbamodel_workspace;
      string fbamodel_id;
      string media_workspace;
      string media_id;
      string genome_workspace;
      string genome_id;
      string proteincomparison_workspace;
      string proteincomparison_id;
      int fill_src;
      int translate_media;
      int num_reactions_to_process;
      string translate_media_workspace;
      string translate_media_id;
      string output_id;
      string workspace;
    } CallingParams;

    typedef structure {
      string report_name;
    	string report_ref;
    } CallingResults;

    /*
     * Morph Function
     */
     funcdef morph_model(CallingParams params) returns (CallingResults) authentication required;
};
