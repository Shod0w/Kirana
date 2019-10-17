(function() 
 {
  var width = 320;    
  var height = 0;     
  
  var streaming = false;

  var video = null;
  var canvas = null;
  var photo = null;
  var startbutton = null;

  function startup()
    {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    photo = document.getElementById('photo');
    startbutton = document.getElementById('startbutton');

    navigator.mediaDevices.getUserMedia({video: true, audio: false})
    .then(function(stream) 
          {
      video.srcObject = stream;
      video.play();
            })
    .catch(function(err) {
      console.log("An error occurred: " + err);
    });

    video.addEventListener('canplay', function(ev)
    {
      if (!streaming) 
      {
        height = video.videoHeight / (video.videoWidth/width);
      
        
        if (isNaN(height)) 
        {
          height = width / (4/3);
        }
      
        video.setAttribute('width', width);
        video.setAttribute('height', height);
        canvas.setAttribute('width', width);
        canvas.setAttribute('height', height);
        streaming = true;
      }
    }, false);

    startbutton.addEventListener('click', function(ev)
    {
      takepicture();
     
      ev.preventDefault();
    }, false);
    
    clearphoto();
  }

  function clearphoto() 
    {
    var context = canvas.getContext('2d');
    context.fillStyle = "#AAA";
    context.fillRect(0, 0, canvas.width, canvas.height);

    var data = canvas.toDataURL('image/png');
    photo.setAttribute('src', data);
    }
     
  function takepicture() 
    {
    var context = canvas.getContext('2d');
    if (width && height) 
    {
      canvas.width = width;
      canvas.height = height;
      context.drawImage(video, 0, 0, width, height);
    
      var data = canvas.toDataURL('image/png');
      photo.setAttribute('src', data);
        
       document.getElementById("photo").style.display = 'block';
        download(data);
       
    } 
        else 
        {
      clearphoto();
        }
      }
    
    function download(blob)
    {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'screenshot.jpg';
        document.body.appendChild(a);
        a.click();
    }
    
  window.addEventListener('load', startup, false);
})();
        