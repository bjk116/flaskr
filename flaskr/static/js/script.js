$( document ).ready(function() {
    console.log( "ready!" );

	$('.addNewComment').click( function(e) {
			e.preventDefault();
			/*your_code_here;*/
			console.log("PRESSED REPLY BUTTON");
			//console.log(e)
			//Get parentComment-# class from button and use it in construction of form
			paths = e.originalEvent.path["0"].classList;
			console.log("PATHS");
			console.log(paths);
			let classToAppend = "";

			for (let i = 0; i < paths.length; i++) {
  				if(paths[i].includes("parentComment")){
  					let commentId = paths[i].split("-")[1];
  					classToAppend = "."+paths[i];
  					console.log("commentId: " + commentId);
  					break;
  				}
			}
			//Append the form to the reply button and relevant HTML
			let replyForm = "<form action=\"{{ url_for('blog.addComment', postId=post['id'], redirectHere=True, parentComment=comment['id'])}}\" method=\"post\">"+
               					"<textarea name=\"comment\"></textarea>"+
                				"<input type=\"submit\">"+
              				"</form>"

			//Append this HTML to the Reply button
			$( replyForm ).insertAfter( classToAppend );
			return false;
		}
	);
});