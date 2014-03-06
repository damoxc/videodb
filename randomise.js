db.video.find().forEach(function(doc) {
    doc._random = Math.random();
    db.video.save(doc);
});
